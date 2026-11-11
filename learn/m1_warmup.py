"""模块 1 第 1 天 · 推导式热身。

每一组都是"同一件事的两种写法"，先看 A 再看 B，
然后 `uv run python learn/m1_warmup.py` 跑一遍，确认结果相同。
"""

from pathlib import Path

# 假装这是 iterdir() 扫出来的文件名（真实场景里是 Path 对象）
names = ["photo1.JPG", "notes.txt", "data.csv", "cover.png", ".keepme", "noext"]

print("=" * 52)
print("① 最简单的：把所有名字取出来")
print("=" * 52)

# A 写法：for + append（你现在 plan() 里的形态）
out_a = []
for n in names:
    out_a.append(n)

# B 写法：列表推导式 —— 把上面三行压成一行
out_b = [n for n in names]

print("A:", out_a)
print("B:", out_b)
print("相同?", out_a == out_b)

print()
print("=" * 52)
print("② 加过滤：只要图片（相当于 for 里那个 if + continue）")
print("=" * 52)

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif")

out_a = []
for n in names:
    if n.lower().endswith(IMAGE_EXTS):
        out_a.append(n)

# 条件写在推导式最后，位置和 for 里的 if 相反——这是最容易记错的地方
out_b = [n for n in names if n.lower().endswith(IMAGE_EXTS)]

print("A:", out_a)
print("B:", out_b)
print("相同?", out_a == out_b)

print()
print("=" * 52)
print("③ 加变形：不是原样收集，而是每个都换一下")
print("=" * 52)

out_b = [n.upper() for n in names if not n.startswith(".")]
print([n.upper() for n in names if not n.startswith(".")])
print("上面这行 = 对每个非隐藏文件名调用 .upper()")

print()
print("=" * 52)
print("④ 字典推导式：反转 FOLDERS")
print("=" * 52)

FOLDERS = {".jpg": "images", ".png": "images", ".txt": "docs", ".csv": "docs"}

# 目标：{images: [.jpg, .png], docs: [.txt, .csv]}
# 一步到位做不到（同一个目录会重复出现），先看"一对仍对一"的错误示范：
bad = {v: k for k, v in FOLDERS.items()}
print("直接反转（丢了数据）:", bad)

# 正确做法：靠 setdefault 累积，这里先用普通循环看清楚逻辑
grouped: dict[str, list[str]] = {}
for ext, target in FOLDERS.items():
    grouped.setdefault(target, []).append(ext)
print("按目录分组:", grouped)

print()
print("=" * 52)
print("⑤ 集合推导式：去重")
print("=" * 52)

targets = [v for v in FOLDERS.values()]
print("列表（有重复）:", targets)
print("集合（自动去重）:", {v for v in FOLDERS.values()})

print()
print("=" * 52)
print("⑥ 三元表达式：不是推导式，但常一起用")
print("=" * 52)

for raw in ["photo1.JPG", "noext", ".keepme"]:
    # 格式：值A if 条件 else 值B，读作"条件成立就给 A，否则给 B"
    kind = "隐藏文件" if raw.startswith(".") else "普通文件"
    print(f"  {raw:12} -> {kind}")

print()
print("  注意 Path('.keepme').suffix 的结果，和你以为的可能不一样：")
for raw in [".keepme", ".jpg"]:
    print(f"    {raw:10} suffix={Path(raw).suffix!r}  stem={Path(raw).stem!r}")
