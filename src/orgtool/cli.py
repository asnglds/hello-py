"""命令行入口：解析参数、执行、汇报。

这一层负责所有「和外界打交道」的事：读命令行、写日志、搬文件。
上面三层（models / rules / planner）都不打印任何东西，
所以它们能被测试和复用；输出只发生在这里。

模块 4 之前这里全是 print。换成 logging 的收益不是「能显示」，
而是能分级、能关掉、能同时写文件、能带上时间戳——print 吐出去就没了。
"""

import argparse
import functools
import logging
import shutil
import time
from collections.abc import Callable
from pathlib import Path

from .models import Move  # noqa: F401  （导出给外部用得上，见 __init__）
from .planner import plan
from .rules import RuleError, RuleSet

# 每个模块一个 logger，名字就是模块的导入路径 orgtool.cli。
# 用 __name__ 而不是硬写字符串：文件被移动或改名时它会自动跟着变。
# 它自己不带 handler——记录会向上冒泡到 setup_logging() 配好的 "orgtool" 父 logger。
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """配置整个包的日志出口。只在 main() 里调用一次。

    为什么在 cli.py 里配：它是唯一知道「用户正在终端里跑」的那一层。
    planner / rules / models 只往 logger 里丢记录，不该决定记录去哪——
    否则这个包被别人 import 时，会擅自改掉人家程序的日志配置。
    """
    # 拿到 "orgtool" 这个父 logger，而不是 logging.getLogger() 拿到的 root logger。
    # 好处：只影响 orgtool.* 的日志，不会把 requests 之类的第三方日志一起改掉。
    orgtool_logger = logging.getLogger("orgtool")
    orgtool_logger.setLevel(logging.INFO)

    # StreamHandler 默认写 stderr。这跟 print 到 stdout 有个真实差别：
    # 以后 `orgtool ... > result.txt` 时，日志不会混进结果文件里。
    handler = logging.StreamHandler()
    # 只打消息本身，不加时间戳和级别——这一关的目标就是「肉眼看不出变化」。
    # 第三关做 --log-file 时，文件那边才换成带时间的详细格式。
    handler.setFormatter(logging.Formatter("%(message)s"))

    orgtool_logger.handlers.clear()  # 防止重复调用时装两遍 handler，输出翻倍
    orgtool_logger.addHandler(handler)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    folder 故意不设默认值。早期版本默认是 "."，
    结果有人在项目目录里直接跑，把项目自己的文件全搬走了。
    让参数必填，就少了一层"意外的默认行为"。
    """
    parser = argparse.ArgumentParser(prog="orgtool", description="按扩展名归档文件")
    parser.add_argument("folder", help="要整理的目录（必填）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不移动文件")
    parser.add_argument(
        "--rules",
        help="规则文件路径（默认使用包内自带的 rules.json）",
    )
    return parser.parse_args()


def retry(times: int = 3, delay: float = 0.2):
    """失败自动重试的装饰器（带参数版，三层结构）。

    只重试 PermissionError —— 也就是「文件正被别的程序占用」这类
    「过一会儿可能就好了」的错误。

    为什么不重试所有 OSError：
    「目标是个目录」「路径不存在」这类错误，重试一百次结果一样，
    白白让每次失败多等 0.4 秒。重试只对「可能自愈」的故障有意义。
    """

    def decorator(func: Callable[..., None]) -> Callable[..., None]:
        @functools.wraps(func)  # 不加这个，func.__name__ 会变成 "wrapper"
        def wrapper(*args: object, **kwargs: object) -> None:
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except PermissionError:
                    if attempt == times:
                        raise  # 最后一次还失败，就让它冒出去，交给上层记录
                    time.sleep(delay)

        return wrapper

    return decorator


@retry(times=3, delay=0.2)
def execute(src: Path, dst: Path) -> None:
    """把单个文件搬到目标位置。失败时抛出 OSError，交给调用方处理。

    单独抽成函数，是为了让 try/except 的范围尽可能小——
    只包住"可能失败的那两行"，不要包住整个循环。
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(src, dst)


def main() -> None:
    setup_logging()  # 必须先于任何日志调用，否则最早的几条会被丢弃

    args = parse_args()
    folder = Path(args.folder)

    # 先确认目录存在，否则后面 iterdir() 会抛出难懂的异常
    if not folder.is_dir():
        logger.error("目录不存在：%s", folder)
        return

    # --rules 不给就用包内自带的 rules.json。
    # Path(__file__) 是「本文件的完整路径」，.with_name() 换成同目录下的另一个文件名。
    # 拆包之前 __file__ 是项目根目录的 organize.py；现在它是 src/orgtool/cli.py，
    # 所以规则文件也跟着搬进了包里——「代码在哪，它自带的资源就在哪」。
    rules_path = Path(args.rules) if args.rules else Path(__file__).with_name("rules.json")
    if not rules_path.is_file():
        logger.error("找不到规则文件：%s", rules_path)
        return

    try:
        rules = RuleSet.from_json(rules_path)
    except RuleError as exc:
        # 异常消息本身已经带了「什么错 + 哪个文件」，直接输出，不再加前缀。
        # 只捕获自定义类型，不写 except (OSError, ValueError)——
        # 那样会把别的环节的错也接住，真正的 bug 会被伪装成「规则文件读不了」。
        logger.error("%s", exc)
        return

    # plan() 返回生成器，不能再 len() 或者先判断非空——那样会把它抽干。
    # 所以改成边遍历边计数，遍历完再判断「一个都没收到」。
    ok = 0
    total = 0
    failed: list[tuple[str, str]] = []

    for move in plan(folder, rules):
        total += 1
        # 试运行：只输出，continue 直接跳到下一个文件
        if args.dry_run:
            # 宽度用 %-20s 而不是 f-string 的 <20：
            # logging 内部就是 msg % args，格式化语法完全通用。
            # 这样既保住了列对齐，又没把字符串提前拼好（惰性格式化的意义）。
            logger.info("[试运行] %-20s -> %s", move.src.name, move.dst.relative_to(folder))
            continue

        # 只捕获 OSError：文件被占用、没权限、目标不可写都属于它。
        # 不写裸 except:，因为那样会把 KeyboardInterrupt 和拼写错误也一起吞掉，
        # 出了 bug 反而更难查。
        try:
            execute(move.src, move.dst)
        except OSError as exc:
            failed.append((move.src.name, str(exc)))
            logger.error("[失败]   %-20s %s", move.src.name, exc)
            continue  # 这一个失败不影响后面的文件

        ok += 1
        logger.info("%-20s -> %s", move.src.name, move.dst.relative_to(folder))

    if total == 0:
        logger.info("没有需要整理的文件。")
        return

    # 最后统一汇报，而不是散落在各处
    logger.info("")
    if args.dry_run:
        logger.info("试运行：共 %s 个文件待整理，未做任何改动。", total)
    elif failed:
        logger.info("完成：成功 %s 个，失败 %s 个", ok, len(failed))
        for name, reason in failed:
            logger.info("  - %s：%s", name, reason)
    else:
        logger.info("完成：成功 %s 个，全部处理完毕。", ok)
