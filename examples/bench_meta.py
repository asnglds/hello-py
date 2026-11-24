"""诊断：并发变慢是不是 8.3 短名生成造成的。

背景：1000 个文件串行 0.39 秒，开 4 个线程变 18 秒。
已经排除杀软、磁盘故障、mkdip 重复调用。剩下的头号嫌疑是 NTFS 的 8.3 短名生成——
它需要在一个卷级的索引里做冲突检测，并发时容易退化成排队。

验证思路（不需要管理员权限，纯行为对比）：
  短名  f0001.jpg                        <= 8.3 规则，不需要生成短名
  长名  very-long-file-name-0001.jpg      > 8.3 规则，必须生成短名

如果只有长名那组在并发下崩掉，就基本可以确定是 8.3 的锅；
如果两组都崩，那就跟 8.3 无关，是 NTFS 元数据写路径本身的序列化。

另外加一组 stat（纯读）做对照：如果读能随线程数扩展、写不能，
就说明瓶颈在「元数据的写」而不是「文件系统整体」。

跑法：
    uv run python examples/bench_meta.py
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WORKERS = 16
COUNT = 1000


def make_files(folder: Path, names: list[str]) -> None:
    folder.mkdir(parents=True, exist_ok=False)
    for name in names:
        (folder / name).write_text("x", encoding="utf-8")


def short_names(count: int) -> list[str]:
    """8.3 兼容的名字：主名 5 个字符，不需要生成短名。"""
    return [f"f{i:04d}.jpg" for i in range(count)]


def long_names(count: int) -> list[str]:
    """超过 8.3 限制的名字：主名 25 个字符，每次创建都要生成短名。"""
    return [f"very-long-file-name-{i:04d}.jpg" for i in range(count)]


def run_serial(fn, items) -> float:
    t0 = time.perf_counter()
    for item in items:
        fn(item)
    return time.perf_counter() - t0


def run_threads(fn, items, workers: int) -> float:
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(fn, items))
    return time.perf_counter() - t0


def rename_once(path: Path) -> None:
    """原地改名：加个前缀，保证目标不存在。"""
    os.rename(path, path.with_name("m_" + path.name))


def stat_once(path: Path) -> None:
    os.stat(path)


def report(label: str, serial: float, threaded: float) -> None:
    ratio = serial / threaded
    verdict = "加速" if ratio > 1.2 else ("持平" if ratio > 0.8 else "变慢")
    print(f"{label:22s} 串行 {serial:6.3f}s  并发 {threaded:7.3f}s  {ratio:5.2f}x  {verdict}")


def main() -> None:
    parser = argparse.ArgumentParser(description="8.3 短名 / 元数据并发诊断")
    parser.add_argument("--root", default=r"D:\pythonCode\playground\diag_meta")
    parser.add_argument("--count", type=int, default=COUNT)
    parser.add_argument("--workers", type=int, default=WORKERS)
    args = parser.parse_args()

    root = Path(args.root)
    if root.exists():
        print(f"目录已存在：{root}")
        print("请先手动清理，或用 --root 换一个路径。")
        sys.exit(1)

    suite = [
        ("短名 rename", short_names(args.count)),
        ("长名 rename", long_names(args.count)),
    ]

    print(f"每轮 {args.count} 个文件，并发 {args.workers} 线程\n")

    for label, names in suite:
        key = "short" if "短" in label else "long"
        # 串行和并发各用一份独立数据：rename 会改掉文件名，不能复用
        case_serial = root / f"{key}_serial"
        make_files(case_serial, names)
        serial = run_serial(rename_once, [case_serial / n for n in names])

        case_thread = root / f"{key}_thread"
        make_files(case_thread, names)
        threaded = run_threads(rename_once, [case_thread / n for n in names], args.workers)

        report(label, serial, threaded)

    # 纯读对照：stat 不改变任何状态，可以复用同一份数据
    case_stat = root / "stat"
    make_files(case_stat, long_names(args.count))
    paths = [case_stat / n for n in long_names(args.count)]
    serial = run_serial(stat_once, paths)
    threaded = run_threads(stat_once, paths, args.workers)
    report("长名 stat（纯读）", serial, threaded)


if __name__ == "__main__":
    main()
