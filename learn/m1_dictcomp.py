"""模块 1 第 2 天 · 字典推导式的边界。

需求：把 FOLDERS（扩展名 -> 目录）反转成（目录 -> 扩展名列表）。

三种写法都能跑出同一个结果，但代价完全不同。
重点看「写法 A 为什么不该用」——那是推导式最典型的误用。
"""

from collections import defaultdict

FOLDERS = {
    ".jpg": "images",
    ".jpeg": "images",
    ".png": "images",
    ".gif": "images",
    ".pdf": "docs",
    ".txt": "docs",
    ".md": "docs",
    ".csv": "docs",
    ".mp4": "videos",
    ".mov": "videos",
    ".avi": "videos",
    ".zip": "archives",
    ".rar": "archives",
    ".7z": "archives",
}

print("=" * 56)
print("先看看硬转会发生什么")
print("=" * 56)
naive = {target: ext for ext, target in FOLDERS.items()}
print("  {v: k for k, v in ...} ->", naive)
print("  15 个扩展名，只剩", len(naive), "个键——同一个目录被后面的覆盖了")

print()
print("=" * 56)
print("写法 A：一行嵌套推导式（能跑，但有问题）")
print("=" * 56)
by_folder_a = {
    target: [ext for ext, t in FOLDERS.items() if t == target]
    for target in set(FOLDERS.values())
}
for k in sorted(by_folder_a):
    print(f"  {k:10} {by_folder_a[k]}")

print()
print("=" * 56)
print("写法 B：循环 + setdefault（推荐）")
print("=" * 56)
by_folder_b: dict[str, list[str]] = {}
for ext, target in FOLDERS.items():
    by_folder_b.setdefault(target, []).append(ext)
for k in sorted(by_folder_b):
    print(f"  {k:10} {by_folder_b[k]}")

print()
print("=" * 56)
print("写法 C：defaultdict（最简洁）")
print("=" * 56)
by_folder_c: defaultdict[str, list[str]] = defaultdict(list)
for ext, target in FOLDERS.items():
    by_folder_c[target].append(ext)
for k in sorted(by_folder_c):
    print(f"  {k:10} {by_folder_c[k]}")

print()
print("=" * 56)
print("三者结果一致吗")
print("=" * 56)
print("  A == B ?", dict(by_folder_a) == dict(by_folder_b))
print("  B == C ?", dict(by_folder_b) == dict(by_folder_c))

print()
print("  但 A 的开销：对每个目录名都重新扫了一遍 FOLDERS")
print("  4 个目录 x 15 个扩展名 = 60 次比对；B 和 C 只用了 15 次")
