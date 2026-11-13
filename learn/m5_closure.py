"""模块 5 上半 · 闭包与最简单的装饰器。

三步走，每步只加一个新东西：
    ① 闭包          函数能记住定义时外层的变量
    ② 装饰器         收一个函数，还一个函数
    ③ 透传参数       被装饰的函数有参数时，包装层必须原样转交
"""

print("=" * 58)
print("① 闭包：内层函数记住了外层的 n")
print("=" * 58)


def make_counter(start: int = 0):
    n = start  # 外层局部变量

    def inc():  # 内层函数
        nonlocal n  # 「我要改的是外层那个 n，不是我自己的」
        n += 1
        return n

    return inc  # 返回的是函数本身，不是调用结果


c1 = make_counter()
c2 = make_counter(10)

print("  c1() ->", c1())
print("  c1() ->", c1())
print("  c1() ->", c1())
print("  c2() ->", c2(), "  ← 各自记各自的 n，互不干扰")

print()
print("  换个角度：make_counter 每次被调用，都会造出一个「新的内存格子」")
print("    c1 记的是 start=0 那个，c2 记的是 start=10 那个")

print()
print("  如果去掉 nonlocal 会怎样：")
print("    内层 n += 1 会被当成「定义一个新的局部变量」，")
print("    Python 直接报 UnboundLocalError——因为它在赋值前就被读取了。")

print()
print("=" * 58)
print("② 装饰器：收一个函数，还一个函数")
print("=" * 58)


def shout(func):
    print(
        f"    [装饰器执行了，时间是「def 的那一刻」，不是调用时] 收到 {func.__name__}"
    )

    def wrapper():
        return func().upper() + "!!!"

    return wrapper  # 注意：返回函数本体，没有括号


@shout
def greet() -> str:
    return "hello"


print("  调用 greet() ->", greet())

print()
print("  @shout 只是语法糖，完全等价于：")
print("    def greet(): ...")
print("    greet = shout(greet)")

print()
print("  所以 greet 这个名字现在指向 wrapper，不是原来的函数：")
print("    greet.__name__ =", greet.__name__, " ← 名字丢了，下一步解决")


print()
print("=" * 58)
print("③ 被装饰的函数有参数：包装层必须透传")
print("=" * 58)


def broken(func):
    def wrapper():  # 只收 0 个参数
        return func()

    return wrapper


@broken
def add(a: int, b: int) -> int:
    return a + b


print("  先看不透传的后果：")
try:
    add(1, 2)
except TypeError as exc:
    print("    add(1, 2) ->", type(exc).__name__, ":", exc)

print()
print("  正确写法：wrapper 用 *args, **kwargs 原样接、原样转")


def logged(func):
    def wrapper(*args: object, **kwargs: object):
        print(f"    [调用 {func.__name__}] 位置参数={args} 关键字参数={kwargs}")
        result = func(*args, **kwargs)
        print(f"    [返回] {result!r}")
        return result

    return wrapper


@logged
def multiply(a: int, b: int = 2) -> int:
    return a * b


print("  multiply(3, 4) ->", multiply(3, 4))
print()
print("  multiply(5) ->", multiply(5))
print()
print("  multiply(a=6, b=7) ->", multiply(a=6, b=7))

print()
print("  *args 收位置参数，**kwargs 收关键字参数，")
print("  再用 * 和 ** 原样转交给 func —— 一个不多、一个不少。")
print("  这样无论被装饰的函数收什么参数，包装层都不用改。")
