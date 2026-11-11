"""模块 1 第 2 天 · 解包。

`*` 和 `**` 只做两件事，方向相反：
    定义时 —— 把散货收进一个容器（pack）
    调用时 —— 把容器拆成散货（unpack）
同一个人，两个方向。这是最容易晕的地方，所以下面成对出现。
"""

print("=" * 56)
print("① 赋值时解包")
print("=" * 56)

pair = ("photo1.JPG", "images/photo1.JPG")
src, dst = pair
print("src =", src)
print("dst =", dst)

# 数量对不上就报错（ValueError，不是 TypeError）
try:
    a, b, c = pair
except ValueError as exc:
    print("a, b, c = pair  ->", type(exc).__name__, ":", exc)

# 不需要的值用下划线接住，这是社区约定："_" = 我不关心
_, just_dst = pair
print("忽略第一个 ->", just_dst)

# 交换两个变量，不需要临时变量
x, y = 1, 2
x, y = y, x
print("交换后 x, y =", x, ",", y)

print()
print("=" * 56)
print("② 星号：收集「剩下的」")
print("=" * 56)

nums = (10, 20, 30, 40)
first, *rest = nums
print("first, *rest      ->", first, rest, "| rest 是", type(rest).__name__)
*head, last = nums
print("*head, last       ->", head, last)

# 星号永远收集成 list，哪怕只剩一个
one, *others = (1, 2)
print("one, *others      ->", one, others, "（只剩一个也是 list）")

print()
print("=" * 56)
print("③ 调用时展开：把容器拆成位置参数")
print("=" * 56)


def move(src: str, dst: str) -> None:
    """假装的搬文件，只为看清参数怎么传进来。"""
    print(f"  move 收到 src={src!r} dst={dst!r}")


print("写死两个参数：")
move("a.txt", "docs/a.txt")

print("用 * 展开一个元组（等价于上一行）：")
move(*pair)

print("用 * 展开一个列表（同样可以）：")
move(*["b.txt", "docs/b.txt"])

print()
print("=" * 56)
print("④ 调用时展开：把字典拆成关键字参数（**）")
print("=" * 56)


def make_dir(path: str, parents: bool = False, exist_ok: bool = False) -> None:
    print(f"  make_dir({path!r}, parents={parents}, exist_ok={exist_ok})")


print("你代码里就是这么写的：")
make_dir("images", parents=True, exist_ok=True)

print("用 ** 展开一个字典（等价）：")
opts = {"parents": True, "exist_ok": True}
make_dir("images", **opts)

print("** 也是合并配置的标准写法：")
defaults = {"parents": False, "exist_ok": False}
override = {"exist_ok": True}
print("  合并后 ->", {**defaults, **override}, "（右边覆盖左边）")

print()
print("=" * 56)
print("⑤ 定义时收集：反过来，把散货收进容器")
print("=" * 56)


def report(*args: object, **kwargs: object) -> None:
    print("  args   =", args, "| 类型", type(args).__name__)
    print("  kwargs =", kwargs, "| 类型", type(kwargs).__name__)


report(1, 2, 3, mode="fast", dry_run=True)
report()

print()
print("  所以一句话：")
print("    定义时  *args   把多余的位置参数收成 tuple")
print("    定义时  **kwargs 把多余的关键字参数收成 dict")
print("    调用时  *lst    把 list/tuple 拆成位置参数")
print("    调用时  **d     把 dict 拆成关键字参数")
