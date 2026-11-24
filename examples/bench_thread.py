"""基准测试：线程池版整理耗时，用来和 bench_serial.py 的基线对比。

和串行版的唯一区别：调用的是 cli.run_concurrent（真实代码路径），
而不是自己在 for 循环里搬。其他条件完全一致——同样的数据、同样的规则、
同样关掉日志输出。

为什么要在计时前把日志级别调高：
串行版压根没打日志（它直接调 execute），如果并发版老老实实打 1000 条 INFO，
比出来的差距里就混进了「打印 1000 行」的成本，那是不公平的对比。
基准测试的原则是：**只改你想测的那个变量。**

跑法：
    uv run python examples/bench_thread.py
    uv run python examples/bench_thread.py --count 5000 --dir D:\\...\\bench_t5
"""

import argparse
import logging
import os
import time
from pathlib import Path

from bench_serial import make_case

from orgtool.cli import run_concurrent
from orgtool.rules import RuleSet


def default_workers() -> int:
    """ThreadPoolExecutor 不传 max_workers 时用的默认值。

    直接照抄 CPython 的实现：min(32, (os.cpu_count() or 1) + 4)。
    打印出来是为了让数字可解释——看到「8 个线程」才知道并发度是多少。
    """
    return min(32, (os.cpu_count() or 1) + 4)


def main() -> None:
    parser = argparse.ArgumentParser(description="orgtool 线程池基准测试")
    parser.add_argument("--count", type=int, default=1000, help="待整理文件数")
    parser.add_argument("--collisions", type=int, default=200, help="制造重名的文件数")
    parser.add_argument(
        "--dir",
        default=r"D:\pythonCode\playground\bench_t",
        help="基准目录（必须不存在，脚本会新建）",
    )
    args = parser.parse_args()

    root = Path(args.dir)
    if root.exists():
        print(f"目录已存在：{root}")
        print("请先手动清理（脚本不会替你删），或用 --dir 换一个路径。")
        return

    rules = RuleSet.from_json(Path(__file__).parents[1] / "src" / "orgtool" / "rules.json")

    print(f"造数据：{args.count} 个文件，其中 {args.collisions} 个制造重名…")
    make_case(root, args.count, args.collisions)

    # 计时开始前静音：基准只测搬运，不测打印
    logging.getLogger("orgtool").setLevel(logging.WARNING)

    t0 = time.perf_counter()
    ok, total, failed = run_concurrent(root, rules)
    elapsed = time.perf_counter() - t0

    print(f"位置          {root}")
    print(f"并发度        {default_workers()} 个线程（Python 默认值）")
    print(f"规划命中      {total} 个")
    print(f"移动成功      {ok} 个，失败 {len(failed)} 个")
    print()
    print(f"合计          {elapsed:8.3f} s   {elapsed / total * 1000:7.3f} ms/个")


if __name__ == "__main__":
    main()
