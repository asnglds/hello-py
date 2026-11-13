"""按扩展名自动归档文件的小工具。

用法：
    uv run python organize.py "D:\\路径\\目标目录" --dry-run    只看计划
    uv run python organize.py "D:\\路径\\目标目录"              真的执行
"""

import argparse
import functools
import json
import os
import shutil
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

# 扩展名 -> 目标子目录的规则，已经搬到 rules.json（跟本文件同目录）。
# 想加新扩展名就改那个 JSON，不需要动代码；想用另一套规则就传 --rules 指定别的文件。


@dataclass(frozen=True)
class Move:
    """一次搬移：从哪到哪。

    用 dataclass 而不是 tuple，唯一理由就是：字段有名字。
    tuple 写成 (src, dst) 时，三个月后看到 moves[3][1] 得靠记忆判断它是谁；
    move.dst 一眼就明白，拼错了 Pylance 还会立刻报红。

    frozen=True 让它不可变，顺带获得可哈希能力（能进 set、能当字典键）。
    """

    src: Path
    dst: Path


class RuleSet:
    """扩展名 -> 目标目录 的映射表，从 JSON 文件加载。

    为什么用普通类而不是 dataclass：
    dataclass 适合「纯数据」，字段是什么、存什么，一眼看完。
    这个类有行为（加载、查表、算属性），而且要在 __init__ 里把键统一转小写，
    用普通类写反而更直接。
    """

    def __init__(self, mapping: dict[str, str]) -> None:
        # 键统一转小写，这样 .JPG 和 .jpg 都能查到。
        # 「统一在入口处归一化」——和 main() 里 str 转 Path 是同一个思路。
        self._mapping = {k.lower(): v for k, v in mapping.items()}

    @classmethod
    def from_json(cls, path: Path) -> "RuleSet":
        """从 JSON 文件读规则。

        为什么不写在 __init__ 里：__init__ 应该只收「已经解析好的数据」。
        读文件可能失败（不存在、格式错），把它放在独立的构造入口里，
        调用方就能明确知道「这一步可能抛异常」，而不是每次造对象都提心吊胆。
        """
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"规则文件应该是一个 JSON 对象，实际是 {type(raw).__name__}：{path}")
        for ext, folder in raw.items():
            if not ext.startswith("."):
                raise ValueError(f"扩展名必须以点开头：{ext!r}（在 {path}）")
            if not isinstance(folder, str):
                raise ValueError(f"目录名必须是字符串：{ext} -> {folder!r}")
        return cls(raw)

    @property
    def extensions(self) -> tuple[str, ...]:
        """所有支持的扩展名，排序后返回。每次读都现算，所以和 _mapping 永远一致。"""
        return tuple(sorted(self._mapping))

    @property
    def folders(self) -> tuple[str, ...]:
        """所有目标目录名，去重且排序。"""
        return tuple(sorted(set(self._mapping.values())))

    def folder_for(self, path: Path) -> str:
        """给一个文件，返回它该去的子目录名；不认识的扩展名归到 others。"""
        return self._mapping.get(path.suffix.lower(), "others")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    folder 故意不设默认值。早期版本默认是 "."，
    结果有人在项目目录里直接跑，把项目自己的文件全搬走了。
    让参数必填，就少了一层"意外的默认行为"。
    """
    parser = argparse.ArgumentParser(description="按扩展名归档文件")
    parser.add_argument("folder", help="要整理的目录（必填）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不移动文件")
    parser.add_argument(
        "--rules",
        help="规则文件路径（默认使用脚本同目录的 rules.json）",
    )
    return parser.parse_args()


def pick_destination(folder: Path, target_dir: str, name: str, taken: set[str]) -> Path:
    """算出目标路径；重名时追加 _1、_2 序号，绝不覆盖已有文件。

    taken 记录本次计划里已经分配出去的路径。
    为什么需要它：只看 dst.exists() 会漏掉"计划内部撞车"的情况——
    比如 photo1.jpg 和 photo1.JPG 都映射到 images/，
    而 Windows 文件名不区分大小写，它们其实是同一个路径。
    """
    stem = Path(name).stem  # 主名，如 photo1
    suffix = Path(name).suffix  # 扩展名，如 .JPG

    dst = folder / target_dir / name
    n = 1
    # normcase 跟着操作系统走：Windows 转小写，Linux 原样返回。
    # 比手写 .lower() 更准确——Linux 上 A.jpg 和 a.jpg 是两个真文件，
    # 硬转小写会把它们误判成冲突。
    while dst.exists() or os.path.normcase(dst) in taken:
        dst = folder / target_dir / f"{stem}_{n}{suffix}"
        n += 1

    taken.add(os.path.normcase(dst))
    return dst


def plan(folder: Path, rules: RuleSet) -> Iterator[Move]:
    """逐个算出"每个文件该搬到哪"，只计算，不动手。

    返回的是生成器：要一个算一个，算完就交出去，不在内存里堆一整份计划。
    十万个文件时，「堆不堆」决定了内存占用是几十兆还是几百字节。

    代价有两个，调用方必须知道：
    1. 只能遍历一次，遍历完就空了
    2. 没有 len()，想统计得自己数

    rules 从参数传进来，不用模块级常量——这样 plan() 不依赖任何全局状态，
    测试时塞一个假的规则表就能跑，不用改磁盘上的文件。
    """
    taken: set[str] = set()

    # 这里仍然先做成列表，故意的。
    # 如果偷懒写成生成器，iterdir() 就会「边遍历边被移动影响」——
    # main() 在拿到第一个 Move 后就开始搬文件、创建 images/ 这类子目录，
    # 而 iterdir() 还没扫完。先快照一份，后面怎么搬都不影响这一轮遍历。
    files = [
        p for p in folder.iterdir() if p.is_file() and not p.name.startswith(".")
    ]

    for item in files:
        dst = pick_destination(folder, rules.folder_for(item), item.name, taken)
        yield Move(item, dst)


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
    args = parse_args()
    folder = Path(args.folder)

    # 先确认目录存在，否则后面 iterdir() 会抛出难懂的异常
    if not folder.is_dir():
        print(f"目录不存在：{folder}")
        return

    # --rules 不给就用脚本旁边的 rules.json。
    # Path(__file__) 是「本文件的完整路径」，.with_name() 换成同目录下的另一个文件名，
    # 这样无论你在哪个目录下运行，都能找到配置文件。
    rules_path = Path(args.rules) if args.rules else Path(__file__).with_name("rules.json")
    if not rules_path.is_file():
        print(f"找不到规则文件：{rules_path}")
        return

    try:
        rules = RuleSet.from_json(rules_path)
    except (OSError, ValueError) as exc:
        # json.JSONDecodeError 是 ValueError 的子类，所以格式错也在这里被接住
        print(f"规则文件读不了：{exc}")
        return

    # plan() 现在返回生成器，不能再 len() 或者先判断非空——那样会把它抽干。
    # 所以改成边遍历边计数，遍历完再判断「一个都没收到」。
    ok = 0
    total = 0
    failed: list[tuple[str, str]] = []

    for move in plan(folder, rules):
        total += 1
        # 试运行：只打印，continue 直接跳到下一个文件
        if args.dry_run:
            print(f"[试运行] {move.src.name:<20} -> {move.dst.relative_to(folder)}")
            continue

        # 只捕获 OSError：文件被占用、没权限、目标不可写都属于它。
        # 不写裸 except:，因为那样会把 KeyboardInterrupt 和拼写错误也一起吞掉，
        # 出了 bug 反而更难查。
        try:
            execute(move.src, move.dst)
        except OSError as exc:
            failed.append((move.src.name, str(exc)))
            print(f"[失败]   {move.src.name:<20} {exc}")
            continue  # 这一个失败不影响后面的文件

        ok += 1
        print(f"{move.src.name:<20} -> {move.dst.relative_to(folder)}")

    if total == 0:
        print("没有需要整理的文件。")
        return

    # 最后统一汇报，而不是散落在各处
    print()
    if args.dry_run:
        print(f"试运行：共 {total} 个文件待整理，未做任何改动。")
    elif failed:
        print(f"完成：成功 {ok} 个，失败 {len(failed)} 个")
        for name, reason in failed:
            print(f"  - {name}：{reason}")
    else:
        print(f"完成：成功 {ok} 个，全部处理完毕。")


if __name__ == "__main__":
    main()
