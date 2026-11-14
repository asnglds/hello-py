"""模块 6 补充 · 容器复杂度（实测版）。

不看大 O 记号，直接跑时间。重点看「规模翻 10 倍，耗时翻几倍」。

结论先行：
    list  按下标取       O(1)
    list  按值查 in      O(n)      ← 越往后越慢
    list  尾部 append    O(1)（均摊）
    list  头部 insert    O(n)      ← 每次都要把后面全部挪一遍
    dict  按键查/插/删   O(1)（平均）
    set   按值查/插/删   O(1)（平均）
"""

import time


def measure(func) -> float:
    """跑一次，返回毫秒。"""
    start = time.perf_counter()
    func()
    return (time.perf_counter() - start) * 1000


print("=" * 60)
print("① 判断「在不在」：list 用扫的，set 用哈希跳")
print("=" * 60)
print(f"  {'规模':>10}  {'list 的 in':>12}  {'set 的 in':>12}  {'快多少倍':>10}")

for n in (10_000, 100_000, 1_000_000):
    data_list = list(range(n))
    data_set = set(data_list)
    target = n - 1  # 最坏情况：排在最后

    t_list = measure(lambda: target in data_list)
    t_set = measure(lambda: target in data_set)
    ratio = t_list / t_set if t_set else float("inf")
    print(f"  {n:>10,}  {t_list:>10.3f} ms  {t_set:>10.4f} ms  {ratio:>8.0f}x")

print()
print("  注意 list 那列：1 万到 100 万，规模 100 倍，耗时也差不多 100 倍。")
print("  set 那列基本不动——它不需要扫，直接算出「该去哪个格子找」。")

print()
print("=" * 60)
print("② 建列表：append 和 insert(0) 差了一个数量级")
print("=" * 60)

N = 50_000


def build_append() -> list[int]:
    out = []
    for i in range(N):
        out.append(i)
    return out


def build_insert0() -> list[int]:
    out = []
    for i in range(N):
        out.insert(0, i)
    return out


t_append = measure(build_append)
t_insert = measure(build_insert0)
print(f"  尾部 append   {t_append:>8.2f} ms")
print(f"  头部 insert   {t_insert:>8.2f} ms  （{t_insert / t_append:.0f} 倍）")
print()
print("  原因：list 是连续内存。插到头部，后面 N 个元素全部要往后挪一格。")
print("  所以「需要一个倒序的列表」应该 append 完再 reverse()，别一个个 insert(0)。")

print()
print("=" * 60)
print("③ 查表：dict vs 两个平行 list")
print("=" * 60)

COUNT = 20_000
keys = [f".ext{i}" for i in range(COUNT)]
values = [f"folder{i}" for i in range(COUNT)]
lookup = dict(zip(keys, values, strict=True))
probe = keys[-1]  # 最后一个，list 最坏情况。注意别叫 target——
# 上面第 32 行已经用 target 装过 int 了，模块级变量的类型在首次赋值时就定死了


def via_list() -> str:
    index = keys.index(probe)  # O(n) 线性扫描
    return values[index]


def via_dict() -> str:
    return lookup[probe]


t1 = measure(via_list)
t2 = measure(via_dict)
print(f"  平行 list（index + 取值）  {t1:>8.4f} ms")
print(f"  dict 直接查键              {t2:>8.4f} ms")
print()
print("  而且平行 list 还有个更致命的问题：两个 list 必须永远同步。")
print("  删一个键忘了删对应的值，下标就全体错位——这种 bug 很难查。")

print()
print("=" * 60)
print("④ 落到你自己的代码上")
print("=" * 60)
print("  taken: set[str]")
print("    → 每个文件都要问「这个目标路径被占了吗」，查 n 次。")
print("      用 list 就是 O(n²)：1000 个文件 100 万次比对；用 set 是 1000 次。")
print()
print("  FOLDERS: dict[扩展名, 目录名]")
print("    → 每个文件查一次，O(1)。用两个平行 list 也能做，但会慢、且易错位。")
print()
print("  moves / files: list")
print("    → 需要保持顺序、需要全部遍历、不需要按值查重。")
print("      这里换成 set 会出错：set 不保证顺序，而「先搬哪个文件」是有意义的；")
print("      而且 set 会自动去重，万一两个文件算出同一个目标路径，就被悄悄吃掉一个。")
print()
print("  一句话：选容器先问「我最频繁的操作是什么」。")
print("    按位置取 → list")
print("    按值查重 → set")
print("    按键取值 → dict")
print("    固定不变的几条数据 → tuple")
