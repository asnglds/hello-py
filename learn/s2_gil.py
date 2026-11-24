"""模块 5 · 关 4：GIL 到底限制了什么。

一句话结论先放这：
    线程能吃「等待」，吃不掉「计算」。

这个脚本用同一个框架跑两类任务，各三遍：
    1. 等 IO   —— time.sleep 假装在读磁盘、等网络
    2. 算 CPU  —— 纯 Python 循环，一点 IO 都没有

每类任务都跑三遍：串行、多线程、多进程。看数字就明白了。

跑法：
    uv run python learn/s2_gil.py
"""

import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

# 任务数和每次的等待时长。8 个任务 × 0.2 秒 = 理论串行 1.6 秒，
# 这个量级足够让差异明显，又不会让你等太久。
TASKS = 8
SLEEP_SECONDS = 0.2
# 纯计算任务的规模：调这个数能让单次计算稳定在零点几秒
CPU_ROUNDS = 3_000_000


def io_task(index: int) -> int:
    """假装在等 IO：睡一会儿，什么也不算。

    time.sleep 会把 GIL 释放掉，所以多个线程可以同时「睡」。
    真实的磁盘读取、网络请求也是这个性质——线程大部分时间在等，
    等的时候不占着解释器。
    """
    time.sleep(SLEEP_SECONDS)
    return index


def cpu_task(index: int) -> int:
    """纯计算：一个累加循环，没有任何等待。

    GIL 限制的是「同一时刻只有一个线程执行 Python 字节码」。
    这种任务里字节码从不间断，所以多线程只能轮流跑、还要额外付出切换开销。
    """
    total = 0
    for i in range(CPU_ROUNDS):
        total += i * i
    return total + index


def serial(fn, n: int) -> float:
    t0 = time.perf_counter()
    for i in range(n):
        fn(i)
    return time.perf_counter() - t0


def threaded(fn, n: int, workers: int) -> float:
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(fn, range(n)))
    return time.perf_counter() - t0


def processed(fn, n: int, workers: int) -> float:
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(fn, range(n)))
    return time.perf_counter() - t0


def report(title: str, fn, workers: int) -> None:
    print(f"\n{title}")
    s = serial(fn, TASKS)
    t = threaded(fn, TASKS, workers)
    p = processed(fn, TASKS, workers)
    print(f"  串行     {s:6.2f} s   基准")
    print(f"  多线程   {t:6.2f} s   {s / t:5.2f}x")
    print(f"  多进程   {p:6.2f} s   {s / p:5.2f}x")


def main() -> None:
    # Windows 上多进程用的是 spawn：子进程会重新 import 这个模块，
    # 所以真正的执行代码必须放在 __main__ 里，否则会无限递归地起进程。
    workers = min(TASKS, mp.cpu_count())
    print(f"任务数 {TASKS}，并发度 {workers}（CPU 逻辑核 {mp.cpu_count()} 个）")

    report("【等 IO 型任务】time.sleep(0.2)，共 8 个", io_task, workers)
    print("  预期：多线程接近 8 倍加速，多进程反而不划算（起进程有固定开销）")

    report("【算 CPU 型任务】纯循环累加，共 8 个", cpu_task, workers)
    print("  预期：多线程没有加速甚至更慢（GIL），多进程才是真并行")


if __name__ == "__main__":
    main()
