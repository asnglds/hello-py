"""模块 6 补充 · 海象运算符 :=

它只解决一个问题：**在「判断」的同时把值存下来，避免算两次。**

为什么要用括号：(x := 值) —— 不加括号在有些位置会产生歧义。
"""

print("=" * 58)
print("① 问题引入：同一个值算两次")
print("=" * 58)


def parse(raw: str) -> int | None:
    """模拟一个有成本的解析：可能失败，返回 None。"""
    print(f"    [parse 被调用] raw={raw!r}")
    return int(raw) if raw.isdigit() else None


items = ["1", "x", "3"]

print("  同一个值算两次的写法：")
result_a = [parse(s) for s in items if parse(s) is not None]
print("  结果:", result_a)
print("  ↑ parse 被调用了 5 次：'1' 和 '3' 各算两次（判断一次、取值一次），")
print("    'x' 只算一次——因为判断时返回 None，没进到取值那一步。")

print()
print("  用海象只算一次：")
result_b = [value for s in items if (value := parse(s)) is not None]
print("  结果:", result_b)
print("  ↑ 只调用了 3 次")

print()
print("  为什么不用普通赋值分开写？因为推导式里没法这么干：")
print("    [value for s in items if (value = parse(s)) is not None]  ← SyntaxError")
print("  普通 = 是「语句」，不能出现在表达式中间；:= 是「表达式」，可以。")

print()
print("=" * 58)
print("② 循环里的经典用法")
print("=" * 58)

print("  老写法：")
print("    while True:")
print("        chunk = f.read(1024)")
print("        if not chunk:")
print("            break")
print("        handle(chunk)")
print()
print("  海象写法：")
print("    while chunk := f.read(1024):")
print("        handle(chunk)")
print()
print("  少了一层缩进，少了一个 break，读起来是一条线。")

print()
print("=" * 58)
print("③ if 里先算再判断")
print("=" * 58)


def find_longest(words: list[str]) -> str | None:
    """找出最长的词，顺便打印它的长度。"""
    if words and (longest := max(words, key=len)):
        print(f"    最长的是 {longest!r}，长度 {len(longest)}")
        return longest
    return None


find_longest(["a", "bbb", "cc"])
find_longest([])

print()
print("  没有海象的话，得先算一次赋给变量，然后 if 里再判断——")
print("  但那个变量会一直留在函数作用域里，哪怕 if 没进去。")
print("  海象让它的生命周期刚好够用。")

print()
print("=" * 58)
print("④ 什么时候别用")
print("=" * 58)
print("  ✗ 为了省一行，把简单逻辑塞进条件里：")
print("      if (n := len(data)) > 10 and (m := n * 2) > 30: ...")
print()
print("  ✗ 在已经够清楚的代码里硬用：")
print("      y = (x := 5) + 1        ← 这里多一个 x 完全没有价值")
print()
print("  ✓ 判断和取值必须用同一个结果时：")
print("      if (match := pattern.search(text)) is not None:")
print("          print(match.group(1))     ← 这里再 search 一次就是浪费")
print()
print("  一句话：它不是「省一行的技巧」，是「避免重复计算的工具」。")
print("  算起来很便宜、或者本来就要分两行写清楚的，别用。")
