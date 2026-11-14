"""规划：算出每个文件该搬到哪。只计算，不碰磁盘。

这一层是整个工具的核心逻辑，也是最容易写测试的一层——
给它一个目录和一份规则，它返回一串 Move，中间没有副作用
（除了读目录和 exists() 判断）。

注意它依赖 rules（要查表）和 models（要构造 Move），
但不依赖 cli。所以想测规划逻辑，不需要装命令行、不需要造参数。
"""

import os
from collections.abc import Iterator
from pathlib import Path

from .models import Move
from .rules import RuleSet


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
    # 调用方在拿到第一个 Move 后就开始搬文件、创建 images/ 这类子目录，
    # 而 iterdir() 还没扫完。先快照一份，后面怎么搬都不影响这一轮遍历。
    files = [
        p for p in folder.iterdir() if p.is_file() and not p.name.startswith(".")
    ]

    for item in files:
        dst = pick_destination(folder, rules.folder_for(item), item.name, taken)
        yield Move(item, dst)
