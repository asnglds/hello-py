"""模块 4 · 生成器。

三个要看清的东西：
    1. yield 到底停在哪儿
    2. 不迭代就什么都不发生（惰性）
    3. 它是一次性的
"""

import sys

print("=" * 56)
print("① yield 暂停在哪：每一句 print 都会告诉你执行到哪了")
print("=" * 56)


def countdown(n: int):
    print("    [函数体开始]")
    while n > 0:
        print(f"    [准备产出 {n}]")
        yield n
        print(f"    [恢复执行，此时 n = {n}]")
        n -= 1
    print("    [函数体结束]")


print("  下面 for 循环开始：")
for value in countdown(3):
    print(f"  >>> 拿到 {value}")

print()
print("=" * 56)
print("② 不迭代，就一行都不会执行")
print("=" * 56)


def loud():
    print("    !!! 函数体被执行了 !!!")
    yield 1
    yield 2


print("  创建生成器：")
g = loud()
print("  创建完了，上面什么都没打印——因为还没人向它要值")

print()
print("  现在手动要一个：")
print("  next(g) ->", next(g))
print("  再一次：")
print("  next(g) ->", next(g))
print("  再来：")
try:
    next(g)
except StopIteration:
    print("    StopIteration：没有更多值了")

print()
print("=" * 56)
print("③ 它是「水管」，不是「水桶」：只能流一遍")
print("=" * 56)

g2 = (x * 2 for x in range(3))
print("  第一次遍历:", [v for v in g2])
print("  第二次遍历:", [v for v in g2], " ← 空了，不是 bug")

print()
print("  对比列表：")
lst = [x * 2 for x in range(3)]
print("  第一次遍历:", [v for v in lst])
print("  第二次遍历:", [v for v in lst])

print()
print("=" * 56)
print("④ 省内存省在哪")
print("=" * 56)

n = 200_000
list_version = [i for i in range(n)]
gen_version = (i for i in range(n))

print(f"  列表推导  {sys.getsizeof(list_version):>9,} 字节")
print(f"  生成器表达式 {sys.getsizeof(gen_version):>7,} 字节")
print(f"  差距：{sys.getsizeof(list_version) / sys.getsizeof(gen_version):.0f} 倍")
print()
print("  而且这个差距和 n 无关——列表随 n 线性增长，生成器永远是那么几十字节。")
print("  它只记住「我算到哪了」，不记住「已经算过什么」。")

print()
print("=" * 56)
print("⑤ 最经典的坑：先检查、再遍历")
print("=" * 56)


def gen_numbers():
    yield from [1, 2, 3]


g3 = gen_numbers()
if not list(g3):          # 想判断「有没有东西」
    print("  空")
else:
    print("  有东西")

print("  然后开始遍历它：")
collected = [x for x in g3]
print("  收到的:", collected, " ← 空的！因为上一步 list() 已经把它抽干了")

print()
print("  列表版本不会有这个问题：")
lst3 = [1, 2, 3]
if not lst3:
    print("  空")
print("  遍历结果:", [x for x in lst3])
