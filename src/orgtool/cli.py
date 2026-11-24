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


def setup_logging(
    *,
    verbose: bool = False,
    quiet: bool = False,
    log_file: str | None = None,
) -> None:
    """配置整个包的日志出口。只在 main() 里调用一次。

    为什么在 cli.py 里配：它是唯一知道「用户正在终端里跑」的那一层。
    planner / rules / models 只往 logger 里丢记录，不该决定记录去哪——
    否则这个包被别人 import 时，会擅自改掉人家程序的日志配置。

    这里有三个独立旋钮：屏幕看多详细（verbose / quiet）、要不要额外写文件（log_file）。
    """
    # 拿到 "orgtool" 这个父 logger，而不是 logging.getLogger() 拿到的 root logger。
    # 好处：只影响 orgtool.* 的日志，不会把 requests 之类的第三方日志一起改掉。
    orgtool_logger = logging.getLogger("orgtool")

    # 关键概念：logger 的 level 是「准入门槛」，handler 的 level 是「这个出口要不要给你看」。
    #   门槛设高 → 记录根本不会产生，性能最好
    #   门槛设低 + 出口自己过滤 → 记录产生了，但只有该看的出口能看到
    # 这里挂 DEBUG（最低），为的是让文件 handler 能拿到全量；
    # 屏幕上显不显示，交给下面各个 handler 自己的 level 决定。
    orgtool_logger.setLevel(logging.DEBUG)

    # 屏幕出口：级别由命令行决定，格式只打消息本身，保持终端干净
    screen_level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    screen = logging.StreamHandler()
    screen.setLevel(screen_level)
    screen.setFormatter(logging.Formatter("%(message)s"))

    orgtool_logger.handlers.clear()  # 防止重复调用时装两遍 handler，输出翻倍
    orgtool_logger.addHandler(screen)

    if log_file:
        path = Path(log_file)
        # 目录不存在就建出来，省得用户先手动 mkdir 再跑一次。
        path.parent.mkdir(parents=True, exist_ok=True)

        # encoding="utf-8" 必须显式写：Windows 上 FileHandler 默认用系统编码（GBK），
        # 中文日志写进去，用 VS Code 或者别的工具打开就是乱码。
        file_handler = logging.FileHandler(path, encoding="utf-8")
        # 文件里永远记全量（DEBUG），跟屏幕级别完全无关。
        # 理由很实际：事后追溯时你不会希望自己「当时怎么没加 -v」。
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                # 文件里才需要这几样：什么时候、什么级别、哪个模块、说了什么。
                # %(name)s 就是 getLogger(__name__) 记下的模块路径，能直接定位到代码。
                "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        orgtool_logger.addHandler(file_handler)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    folder 故意不设默认值。早期版本默认是 "."，
    结果有人在项目目录里直接跑，把项目自己的文件全搬走了。
    让参数必填，就少了一层"意外的默认行为"。
    """
    parser = argparse.ArgumentParser(prog="orgtool", description="按扩展名归档文件")
    parser.add_argument("folder", help="要整理的目录（必填）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不移动文件")

    # -v 和 -q 互斥：同时指定就是自相矛盾。
    # 用 mutually_exclusive_group 让 argparse 替你拒绝，比在代码里 if 判断干净。
    volume = parser.add_mutually_exclusive_group()
    volume.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="输出每个文件的决策过程（DEBUG 级别）",
    )
    volume.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="屏幕上只输出错误（WARNING 及以上）",
    )
    parser.add_argument(
        "--log-file",
        help="把全量日志（含 DEBUG）写入文件，与屏幕级别无关",
    )
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
    # 顺序有讲究：先解析参数，才知道要不要 DEBUG、要不要写文件；
    # 但 parse_args 本身不写日志，所以把它放前面是安全的。
    args = parse_args()
    # 必须先于任何日志调用，否则最早的几条会被丢弃——
    # 这就是为什么 setup_logging 是 main() 里第一个「有副作用」的动作。
    setup_logging(verbose=args.verbose, quiet=args.quiet, log_file=args.log_file)

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
            # 屏幕只留一句话：用户关心的是「哪几个没搬成」，不是调用栈。
            logger.error("[失败]   %-20s %s", move.src.name, exc)
            # 完整 traceback 走 DEBUG：默认屏幕上不显示，但 --log-file 里一定有。
            # exc_info=True 会把异常类型、消息、调用栈一并附在记录上。
            # 它必须在 except 块内部调用——离开这个块，异常上下文就没了，
            # 拿到的是 None，日志里只会打出一句 "NoneType: None"。
            logger.debug("失败详情：%s", move.src.name, exc_info=True)
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
