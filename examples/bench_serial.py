"""基准测试：把 N 个文件整理一遍，分别计时。

模块 5 的第一件事不是加并发，而是**拿到串行基线**。
没有这个数字，后面加线程池就只能靠感觉说「好像快了」——
感觉不是结论，数字才是。

跑法：
    uv run python examples/bench_serial.py
    uv run python examples/bench_serial.py --count 5000 --collisions 500

脚本只读自己造的那批文件，不会碰目录里别的东西。
目录已存在时不会自动删除，需要你手动清理后重跑——
自动删除别人目录里的东西，是脚本最不该有的「贴心」。
"""

import argparse
import time
from pathlib import Path

from orgtool.cli import execute
from orgtool.planner import plan
from orgtool.rules import RuleSet

# 和 rules.json 保持一致的扩展名分布：4 个目标目录、17 种扩展名。
# 用真实分布而不是清一色 .jpg，是为了让 plan() 里「查表」的代价也算进去。
EXTENSIONS: list[tuple[str, str]] = [
    (".jpg", "images"),
    (".jpeg", "images"),
    (".png", "images"),
    (".gif", "images"),
    (".webp", "images"),
    (".pdf", "docs"),
    (".txt", "docs"),
    (".md", "docs"),
    (".csv", "docs"),
    (".docx", "docs"),
    (".xlsx", "docs"),
    (".mp4", "videos"),
    (".mov", "videos"),
    (".avi", "videos"),
    (".zip", "archives"),
    (".rar", "archives"),
    (".7z", "archives"),
]

CONTENT = "benchmark payload\n"


def make_case(root: Path, count: int, collisions: int) -> None:
    """造一批待整理的文件，外加若干「目标位置已被占用」的陷阱。

    为什么要故意制造重名：
    真实场景里，第二次运行 orgtool 时目标目录往往已经有同名文件，
    走的是 pick_destination 的改名分支（a.jpg -> a_1.jpg）。
    如果基准里没有这种文件，测出来的只是「最顺利的那条路径」。
    """
    root.mkdir(parents=True, exist_ok=False)

    names: list[tuple[str, str]] = []
    for i in range(count):
        ext, folder = EXTENSIONS[i % len(EXTENSIONS)]
        name = f"file_{i:05d}{ext}"
        names.append((name, folder))
        (root / name).write_text(CONTENT, encoding="utf-8")

    # 前 collisions 个文件，提前在它们的「目标目录」里放一个同名文件。
    # plan() 算目标时会发现 dst.exists()，于是走改名分支，文件名多出 _1。
    for name, folder in names[:collisions]:
        target_dir = root / folder
        target_dir.mkdir(exist_ok=True)
        (target_dir / name).write_text("already here\n", encoding="utf-8")


def bench(root: Path, rules: RuleSet) -> None:
    """分三段计时：规划、移动、合计。"""
    count = sum(1 for p in root.iterdir() if p.is_file())

    # 阶段一：只算不动。plan() 是生成器，必须 list() 抽干才算完整耗时——
    # 只创建生成器不遍历的话，测到的是「什么都没做」。
    t0 = time.perf_counter()
    moves = list(plan(root, rules))
    t1 = time.perf_counter()

    # 阶段二：真的搬。逐个捕获 OSError，别让一个失败中断整轮统计。
    moved = 0
    renamed = 0
    failed = 0
    for move in moves:
        if move.dst.name != move.src.name:
            renamed += 1
        try:
            execute(move.src, move.dst)
        except OSError:
            failed += 1
            continue
        moved += 1
    t2 = time.perf_counter()

    plan_s = t1 - t0
    move_s = t2 - t1
    total_s = t2 - t0

    print(f"文件数        {count}")
    print(f"规划命中      {len(moves)} 个（其中重名改名 {renamed} 个）")
    print(f"移动成功      {moved} 个，失败 {failed} 个")
    print()
    print(f"规划阶段      {plan_s:8.3f} s   {plan_s / count * 1000:7.3f} ms/个")
    print(f"移动阶段      {move_s:8.3f} s   {move_s / count * 1000:7.3f} ms/个")
    print(f"合计          {total_s:8.3f} s   {total_s / count * 1000:7.3f} ms/个")
    print()
    print(f"移动阶段占总耗时 {move_s / total_s * 100:.1f}%  ← 这个比例决定并发有没有意义")


def main() -> None:
    parser = argparse.ArgumentParser(description="orgtool 串行基准测试")
    parser.add_argument("--count", type=int, default=1000, help="待整理文件数")
    parser.add_argument("--collisions", type=int, default=200, help="制造重名的文件数")
    parser.add_argument(
        "--dir",
        default=r"D:\pythonCode\playground\bench",
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
    print(f"位置：{root}")
    print()

    bench(root, rules)


if __name__ == "__main__":
    main()
