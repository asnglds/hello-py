"""模块 6 下半 · is 与 ==。

一句话：
    ==  比「内容一样吗」   → 调用 __eq__
    is  比「是不是同一个东西」 → 比 id

昨天那个 id() 实验就是 is 的全部真相。
"""

print("=" * 58)
print("① 两个列表：内容一样，但不是同一个")
print("=" * 58)

a = [1, 2, 3]
b = [1, 2, 3]
c = a

print("  a == b ->", a == b, "  （内容相同）")
print("  a is b ->", a is b, "（两个不同的对象）")
print("  a is c ->", a is c, "（c 就是 a 的另一个名字）")
print()
print("  id 对照：")
print("    id(a) =", id(a))
print("    id(b) =", id(b))
print("    id(c) =", id(c), " ← 和 a 相同")

print()
print("=" * 58)
print("② 小整数缓存：-5 ~ 256 之间，同一个对象被反复使用")
print("=" * 58)

x = 200
base = 199
y = base + 1  # 运行时计算，造一个新的 int 对象（但落进缓存区间）
print("  x = 200, base = 199, y = base + 1")
print("  x == y ->", x == y)
print("  x is y ->", x is y, " ← True，因为 200 在缓存区间内，返回的是同一个对象")

print()
p = 257
base2 = 256
q = base2 + 1  # 同样是运行时计算，但 257 超出缓存
print("  p = 257, base2 = 256, q = base2 + 1")
print("  p == q ->", p == q)
print("  p is q ->", p is q, " ← False，超出 -5~256，是两个独立对象")

print()
print("  这个缓存是 CPython 的实现细节，不是语言规定。")
print("  别的实现（PyPy 等）可能不一样 —— 所以永远不要依赖它。")

print()
print("=" * 58)
print("③ 字符串驻留：长得像标识符的短字符串会被复用")
print("=" * 58)

s1 = "hello"
s2 = "".join(["hel", "lo"])  # 运行时拼出来，不是字面量
print('  s1 = "hello"')
print('  s2 = "".join(["hel", "lo"])')
print("  s1 == s2 ->", s1 == s2)
print("  s1 is s2 ->", s1 is s2, " ← 内容一样，但不是同一个对象")

print()
print("  同样是实现细节，同样不可依赖。")
print("  结论只有一条：比较字符串永远用 ==。")

print()
print("=" * 58)
print("④ 什么时候必须用 is：拿「唯一标识」比较时")
print("=" * 58)

value = None
print("  value = None")
print("  value is None     ->", value is None, " ✅ 推荐")
print("  value == None     ->", value == None, " ⚠️ 能用但别写")  # noqa: E711

print()
print("  为什么 == None 不安全？看这个类：")


class Weird:
    def __eq__(self, other: object) -> bool:
        return True  # 跟谁比都说「相等」


w = Weird()
print("    w == None ->", w == None, " ← 你信这个结果吗")  # noqa: E711
print("    w is None ->", w is None, " ← 这个才是事实")

print()
print("  == 走的是 __eq__，可以被任何类重写成任意逻辑。")
print("  is 走的是 id 比较，谁也改不了。")
print("  所以判断 None、True、False、哨兵对象，一律用 is。")

print()
print("=" * 58)
print("⑤ 一个真实的 bug")
print("=" * 58)


def find_bad(items: list[int], target: int) -> int | None:
    """错版：用 is 比数值。"""
    for index, value in enumerate(items):
        if value is target:
            return index
    return None


def find_good(items: list[int], target: int) -> int | None:
    """对版：用 == 比数值。"""
    for index, value in enumerate(items):
        if value == target:
            return index
    return None


data_base = 999
data = [1, 2, data_base + 1]  # 运行时算出来的 1000，不是字面量常量

print("  data =", data, "，找 1000")
print("    find_bad  ->", find_bad(data, 1000), " ← 找不到！明明就在里面")
print("    find_good ->", find_good(data, 1000))

print()
print("  注意 data 里那个 1000 是 data_base + 1 算出来的，")
print("  而传进去的 1000 是字面量——两个不同的 int 对象，所以 is 不成立。")
print("  （如果两边都写成字面量 1000，CPython 会把常量去重，反而碰巧对了）")

print()
print("  再找 2（落在小整数缓存里）：")
print("    find_bad  ->", find_bad(data, 2), " ← 居然找对了")
print("    find_good ->", find_good(data, 2))
print()
print("  这才是最可怕的地方：< 256 的值能过，>= 256 的值失效，")
print("  而结果还取决于那个数字是字面量还是算出来的。")
print("  测试时用小数字一切正常，上线碰到大数字就悄悄丢数据。")

print()
print("=" * 58)
print("⑥ 一张判断表")
print("=" * 58)
print("  比内容（数字、字符串、列表、字典、自己的对象） -> ==")
print("  比身份（None、True、False、哨兵 object()）      -> is")
print()
print("  记忆口诀：")
print("    想知道「它们相等吗」      -> ==")
print("    想知道「是不是同一个」    -> is")
print("    绝大多数业务代码里，你要问的都是前者。")
