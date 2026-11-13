"""模块 3 第 1 步 · @property 与 @classmethod。

两个装饰器各解决一个问题：
    @property    —— 让它「用起来像字段，实际上是现算的」
    @classmethod —— 让它「多一个入口」，不止 __init__ 一种构造方式
"""

print("=" * 56)
print("① 不加 @property：每次要括号")
print("=" * 56)


class A:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def folders(self) -> list[str]:
        return sorted(set(self.mapping.values()))


a = A({".jpg": "images", ".png": "images", ".txt": "docs"})
print("  a.folders()  ->", a.folders(), " ← 要写括号，说明它是动作")

print()
print("=" * 56)
print("② 加 @property：像字段一样用")
print("=" * 56)


class B:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    @property
    def folders(self) -> list[str]:
        return sorted(set(self.mapping.values()))


b = B({".jpg": "images", ".png": "images", ".txt": "docs"})
print("  b.folders    ->", b.folders, " ← 不写括号，读起来像属性")

print()
print("  但它是「现算的」，不是存下来的——每读一次就跑一遍：")
b.mapping[".zip"] = "archives"
print("  往 mapping 加一项后，b.folders ->", b.folders, "（自动跟着变）")

print()
print("  如果硬要去调用它，会报错：")
try:
    b.folders()
except TypeError as exc:
    print("    b.folders() ->", type(exc).__name__, ":", exc)

print()
print("=" * 56)
print("③ @property 的另一个用处：控制写入")
print("=" * 56)


class C:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    @property
    def extensions(self) -> list[str]:
        return sorted(self.mapping)

    @property
    def count(self) -> int:
        return len(self.mapping)


c = C({".jpg": "images", ".txt": "docs"})
print("  c.extensions ->", c.extensions)
print("  c.count      ->", c.count)
try:
    c.count = 99
except AttributeError as exc:
    print("  c.count = 99 ->", type(exc).__name__, ":", exc)
print("  没有 setter，它就是只读的")

print()
print("=" * 56)
print("④ @classmethod：第二种构造方式")
print("=" * 56)


class D:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    @classmethod
    def from_pairs(cls, text: str) -> "D":
        """把 "a=b,c=d" 这种字符串解析成对象。

        为什么要它：__init__ 只收「已经解析好的 dict」。
        从字符串、从文件、从网络读都要先解析一步，
        这一步放外面很啰嗦，放进来就成了「另一个构造入口」。
        """
        pairs = (chunk.split("=") for chunk in text.split(","))
        return cls({k.strip(): v.strip() for k, v in pairs})

    def __repr__(self) -> str:
        return f"D(mapping={self.mapping!r})"


d = D.from_pairs("jpg=images, png=images, txt=docs")
print("  D.from_pairs(...) ->", d)

print()
print("  cls 是谁？看返回值类型，它自动是当前类：")
print("  所以子类调用时会造出子类，而不是写死 D —— 这是 cls 和 D 的区别")

print()
print("=" * 56)
print("⑤ 三者对照：什么时候用哪个")
print("=" * 56)
print("  __init__        唯一的「正式构造」入口，收已解析好的参数")
print("  @classmethod    额外的构造入口，名字以 from_ 开头是惯例")
print("  @property       无参、只读、现算的属性")
print("  普通方法        需要参数、或者是有动作的事")
