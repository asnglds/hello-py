"""诊断：线程数对整理耗时的影响，附带「目录预建」对照。

背景：一次真实测量里，1000 个文件串行 0.54 秒，16 线程却要 18.8 秒——
慢了 35 倍。并发不但没加速，反而把程序弄坏了。这个脚本用来定位原因。

两种模式：
  full  按生产代码的方式搬（每个文件都调 mkdir + shutil.move，跟 cli.move_file 一致）
  fast  目录预先建好，只做 os.rename（去掉 mkdir 这一层）

对比这两个模式，就能分清慢在「线程争用」还是慢在「重复 mkdir」。

跑法（在你自己的终端里跑，不要在我的沙箱里跑）：
    uv run python examples/bench_workers.py
"""

import argparse
import logging
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bench_serial import make_case

from orgtool.models import Move
from orgtool.planner import plan
from orgtool.rules import RuleSet

WORKER_CHOICES = (1, 2, 4, 8, 16)


def move_full(move: Move) -> None:
    """生产路径的等价物：先确保目标目录存在，再搬。"""
    move.dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(move.src, move.dst)


def move_fast(move: Move) -> None:
    """对照路径：目录已经建好，只做一次 rename。

    shutil.move 在同一分区上的本质就是 os.rename，
    区别只是它多做了「源和目标是不是同一个文件」之类的检查。
    这里直接 os.rename，把 mkdir 和那些检查统统去掉。
    """
    os.rename(move.src, move.dst)


def precreate_dirs(moves: list[Move]) -> None:
    """把这次计划会用到的所有目标目录一次性建好。"""
    for target in {m.dst.parent for m in moves}:
        target.mkdir(parents=True, exist_ok=True)


def measure(folder: Path, moves: list[Move], workers: int, *, fast: bool) -> float:
    """用 workers 个线程跑完这批 move，返回耗时（秒）。"""
    fn = move_fast if fast else move_full
    t0 = time.perf_counter()
    if workers == 1:
        # 单线程直接循环，不经过线程池——否则测到的是「线程池的 1 线程」，
        # 而不是「完全没有并发的串行」。这两者的开销不一样，基准要干净。
        for move in moves:
            fn(move)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(fn, moves))
    return time.perf_counter() - t0


def main() -> None:
    parser = argparse.ArgumentParser(description="线程数曲线诊断")
    parser.add_argument("--count", type=int, default=1000, help="每轮的文件数")
    parser.add_argument("--collisions", type=int, default=200, help="制造重名的文件数")
    parser.add_argument(
        "--root",
        default=r"D:\pythonCode\playground\diag_workers",
        help="诊断根目录（必须不存在）",
    )
    parser.add_argument(
        "--workers",
        default="1,2,4,8,16",
        help=f"要测的线程数，逗号分隔，默认 {','.join(map(str, WORKER_CHOICES))}",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if root.exists():
        print(f"目录已存在：{root}")
        print("请先手动清理，或用 --root 换一个路径。")
        sys.exit(1)

    workers_list = [int(w) for w in args.workers.split(",")]
    rules = RuleSet.from_json(Path(__file__).parents[1] / "src" / "orgtool" / "rules.json")
    logging.getLogger("orgtool").setLevel(logging.WARNING)

    print(f"每轮 {args.count} 个文件，其中 {args.collisions} 个重名\n")
    print(f"{'模式':6s} {'线程':>4s} {'耗时(s)':>9s} {'ms/个':>8s} {'相对串行':>9s}")
    print("-" * 42)

    for fast in (False, True):
        label = "fast" if fast else "full"
        serial_time: float | None = None
        for workers in workers_list:
            case = root / f"{label}_w{workers}"
            make_case(case, args.count, args.collisions)
            moves = list(plan(case, rules))
            if fast:
                # fast 模式要求目录已存在，否则 os.rename 会失败
                precreate_dirs(moves)

            elapsed = measure(case, moves, workers, fast=fast)
            if serial_time is None:
                serial_time = elapsed
            ratio = serial_time / elapsed
            print(
                f"{label:6s} {workers:4d} {elapsed:9.3f} {elapsed / args.count * 1000:8.3f} "
                f"{ratio:8.2f}x"
            )
        print()


if __name__ == "__main__":
    main()
