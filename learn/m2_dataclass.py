"""模块 2 第 1 步 · dataclass 到底省了什么。

同一个「一次搬移」的数据，先手写类，再换成 dataclass，对比四个维度：
写法长度 / print 输出 / 相等判断 / 能不能当字典键。
"""

from dataclasses import dataclass, field

print("=" * 58)
print("① 手写类：想要「打印好看 + 能比较」，得自己写 3 个 dunder")
print("=" * 58)


class MoveManual:
    def __init__(self, src: str, dst: str) -> None:
        self.src = src
        self.dst = dst

    # 不写 __repr__，print 出来就是内存地址
    # 不写 __eq__，两个内容相同的实例永远不相等


m1 = MoveManual("a.jpg", "images/a.jpg")
m2 = MoveManual("a.jpg", "images/a.jpg")
print("  print(m1)   ->", m1)
print("  m1 == m2    ->", m1 == m2, "（内容一样，但判为不等）")


print()
print("=" * 58)
print("② 还是手写，把三个 dunder 补齐（12 行）")
print("=" * 58)


class MoveFull:
    def __init__(self, src: str, dst: str) -> None:
        self.src = src
        self.dst = dst

    def __repr__(self) -> str:
        return f"MoveFull(src={self.src!r}, dst={self.dst!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MoveFull):
            return NotImplemented
        return (self.src, self.dst) == (other.src, other.dst)

    def __hash__(self) -> int:
        return hash((self.src, self.dst))


m3 = MoveFull("a.jpg", "images/a.jpg")
m4 = MoveFull("a.jpg", "images/a.jpg")
print("  print(m3)   ->", m3)
print("  m3 == m4    ->", m3 == m4)
print("  放进 set    ->", {m3, m4}, "（只留一个）")


print()
print("=" * 58)
print("③ dataclass：同样三个 dunder，自动生成（4 行）")
print("=" * 58)


@dataclass(frozen=True)
class Move:
    src: str
    dst: str


m5 = Move("a.jpg", "images/a.jpg")
m6 = Move("a.jpg", "images/a.jpg")
print("  print(m5)   ->", m5)
print("  m5 == m6    ->", m5 == m6)
print("  放进 set    ->", {m5, m6}, "（只留一个）")

print()
print("  字段有名字，不用记位置：")
print("    m5.src =", m5.src)
print("    m5.dst =", m5.dst)

print()
print("  frozen=True 的效果：")
try:
    m5.src = "b.jpg"
except Exception as exc:
    print("    改字段 ->", type(exc).__name__, ":", exc)


print()
print("=" * 58)
print("④ 默认值的坑：可变默认值")
print("=" * 58)


class PlainBad:
    """普通类：可变默认值会被所有实例共享，而且不报错。"""

    def __init__(self, items: list[str] = []) -> None:  # noqa: B006
        self.items = items


b1, b2 = PlainBad(), PlainBad()
b1.items.append("x")
print("  普通类 b1 加了一项，b2 也变了 ->", b2.items)

print()
print("  但 dataclass 会直接拒绝这种写法：")
try:

    @dataclass
    class BadDC:
        items: list[str] = []

except ValueError as exc:
    print("    定义报错 -> ValueError:", exc)

print()
print("  正确写法：用 field(default_factory=list)")
print("  意思是「每个实例创建时，各自调用一次 list()」")


@dataclass
class GoodDC:
    items: list[str] = field(default_factory=list)


g1, g2 = GoodDC(), GoodDC()
g1.items.append("x")
print("    g1.items =", g1.items)
print("    g2.items =", g2.items, "（互不影响）")


print()
print("=" * 58)
print("⑤ order=True：让实例能排序")
print("=" * 58)


@dataclass(order=True)
class Sized:
    size: int
    name: str


items = [Sized(30, "c"), Sized(10, "a"), Sized(20, "b")]
print("  排序前:", [i.name for i in items])
print("  排序后:", [i.name for i in sorted(items)])
