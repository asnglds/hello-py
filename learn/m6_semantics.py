"""模块 6 上半 · 一个病，三种症状。

病根：**变量存的不是对象本身，是「对象在哪」的地址。**
赋值复制的是地址，不是内容。所以两个名字可以指向同一个列表。

看起来没事，是因为 int / str / tuple 都不可变——
你对它们做的每一次「修改」，实际都是新建一个对象。
"""

import copy

print("=" * 58)
print("① 症状一：def f(x=[]) —— 默认值只造了一次")
print("=" * 58)


def bad(items: list[int] = []) -> list[int]:  # noqa: B006
    items.append(1)
    return items


print("  bad() ->", bad())
print("  bad() ->", bad())
print("  bad() ->", bad())
print()
print("  每次调用都往里加，因为它从头到尾只造过一个列表。")
print("  证据在这里 —— 默认值本身已经被改了：")
print("    bad.__defaults__ =", bad.__defaults__)
print()
print("  正确写法：")
print("    def good(items: list[int] | None = None):")
print("        if items is None:")
print("            items = []")
print("  或者用 dataclass 时的 field(default_factory=list)。")

print()
print("=" * 58)
print("② 症状二：b = a 不是复制，是「再取个小名」")
print("=" * 58)

a = [1, 2, 3]
b = a  # 没有复制任何东西
b.append(4)

print("  a =", a)
print("  b =", b)
print()
print("  它们根本就是同一个东西：")
print("    id(a) =", id(a))
print("    id(b) =", id(b), " ← 一模一样")
print()
print("  想让 b 独立，必须显式复制：")
c = a.copy()
c.append(999)
print("    c = a.copy() 之后 c.append(999)")
print("    a =", a, " ← 没受影响")

print()
print("=" * 58)
print("③ 症状三：浅拷贝只「新了一层」")
print("=" * 58)

matrix = [[1, 2], [3, 4]]
shallow = matrix[:]  # 切片是浅拷贝
print("  matrix  =", matrix)
print("  shallow =", shallow)
print("  外层是不同的列表：")
print("    id(matrix) =", id(matrix))
print("    id(shallow) =", id(shallow))
print("  但内层是同一批：")
print("    id(matrix[0]) =", id(matrix[0]))
print("    id(shallow[0]) =", id(shallow[0]), " ← 一样")
print()
shallow[0][0] = 99
print("  shallow[0][0] = 99 之后：")
print("    matrix  =", matrix, " ← 被改了")
print("    shallow =", shallow)
print()
print("  但整个替换一个内层，就不影响了：")
shallow[1] = [7, 8]
print("    shallow[1] = [7, 8] 之后 matrix =", matrix)

print()
print("=" * 58)
print("④ 深拷贝：所有层都新造")
print("=" * 58)

matrix2 = [[1, 2], [3, 4]]
deep = copy.deepcopy(matrix2)
deep[0][0] = 99
print("  deepcopy 之后改内层：")
print("    matrix2 =", matrix2, " ← 没受影响")
print("    deep     =", deep)
print()
print("  代价：deepcopy 要递归走完整个结构，比浅拷贝慢得多。")
print("  只在「真的需要独立副本」时用。")

print()
print("=" * 58)
print("⑤ 最隐蔽的一个：[[0]*3]*3")
print("=" * 58)

grid = [[0] * 3] * 3
print("  grid =", grid)
print("  想把左上角改成 1：")
grid[0][0] = 1
print("  grid[0][0] = 1 ->", grid)
print()
print("  三行全变了。因为 *3 复制的是「同一个列表的地址」：")
print("    [id(row) for row in grid] =", [id(row) for row in grid])
print()
print("  正确写法：")
right = [[0] * 3 for _ in range(3)]
right[0][0] = 1
print("    [[0]*3 for _ in range(3)] ->", right)
print("    三个内层 id 各不相同:", [id(row) for row in right])
print()
print("  记住这个区别：")
print("    [x] * 3        复制同一个东西三份（引用）")
print("    [f() for _ ...] 每次重新求值（新对象）")
