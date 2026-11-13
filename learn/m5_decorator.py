"""模块 5 下半 · functools.wraps 与带参数的装饰器。

两件事：
    ① wraps      : 别把原函数的名字和文档弄丢
    ② 带参数的装饰器: 三层结构，比无参版多套一层
"""

import functools
import time

print("=" * 58)
print("① 不加 wraps 会丢什么")
print("=" * 58)


def plain(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def with_wraps(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@plain
def transfer(amount: int, to: str) -> str:
    """把 amount 元转给 to。"""
    return f"转出 {amount} 给 {to}"


@with_wraps
def transfer2(amount: int, to: str) -> str:
    """把 amount 元转给 to。"""
    return f"转出 {amount} 给 {to}"


for f in (transfer, transfer2):
    print(f"  {f.__name__:10} 文档={f.__doc__!r}")

print()
print("  不加 wraps 的那个，名字变成了 wrapper、文档变成了 None。")
print("  wraps 做的事：把原函数的 __name__ / __doc__ / __module__ / __annotations__")
print("  复制到 wrapper 上，再给 wrapper 加一个 __wrapped__ 指回原函数。")

print()
print("=" * 58)
print("② 带参数的装饰器：多套一层")
print("=" * 58)

call_log: list[str] = []


def retry(times: int = 3, delay: float = 0.05):
    """返回一个装饰器。注意它自己不装饰函数，它生产装饰器。"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error: Exception | None = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except OSError as exc:
                    last_error = exc
                    call_log.append(f"{func.__name__} 第 {attempt} 次失败")
                    print(f"    第 {attempt} 次失败：{exc}")
                    if attempt < times:
                        time.sleep(delay)
            print(f"    重试 {times} 次都失败了，放弃")
            raise last_error  # type: ignore[misc]

        return wrapper

    return decorator


flaky_state = {"count": 0}


@retry(times=3, delay=0.01)
def open_locked_file(path: str) -> str:
    """前两次假装被占用，第三次成功。"""
    flaky_state["count"] += 1
    if flaky_state["count"] < 3:
        raise OSError(f"[WinError 32] 另一个程序正在使用此文件：{path}")
    return f"读到了 {path}"


print("  调用 open_locked_file('a.txt'):")
print("  返回 ->", open_locked_file("a.txt"))
print()
print("  调用记录:")
for line in call_log:
    print("   ", line)

print()
print("  再调用一次（这次第一次就成功，因为 count 已经到 3）:")
print("  返回 ->", open_locked_file("a.txt"))

print()
print("=" * 58)
print("③ 三层结构和两层结构差在哪")
print("=" * 58)
print("  两层  @deco         deco(func)              -> wrapper")
print("  三层  @deco(x)      deco(x) -> decorator    -> decorator(func) -> wrapper")
print()
print("  所以 @retry 和 @retry() 是两回事：")
print("    @retry        -> retry(func)，把函数当成了 times 参数 → 后面必然炸")
print("    @retry()      -> retry() 先返回 decorator，再用它装饰 → 正确")

print()
print("  验证（三步走，注意哪一步才炸）：")
bad = retry(open)                 # 第 1 步：times 收到了一个函数，此时不报错
wrapped = bad(lambda: "假装是个函数")  # 第 2 步：装饰也完成了，还不报错
print("    前两步都没报错——因为装饰只是「装配」，不执行 wrapper")
try:
    wrapped()                     # 第 3 步：真正调用，range(1, open + 1) 才炸
except TypeError as exc:
    print("    调用时才炸 ->", type(exc).__name__, ":", exc)
print()
print("  这就是「装饰是装配阶段、调用是运行阶段」最直观的例子：")
print("  参数写错了，错误也要等到运行时才出现。")
