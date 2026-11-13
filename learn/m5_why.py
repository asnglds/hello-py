"""模块 5 补充 · 闭包和装饰器到底解决什么问题。

不看机制，只看「没有它们会怎样」。
"""

import time

print("=" * 58)
print("① 闭包：把配置「冻」进函数里")
print("=" * 58)


def make_rounder(digits: int):
    """造一个「固定保留 N 位小数」的函数。"""

    def round_it(value: float) -> float:
        return round(value, digits)  # 这里的 digits 来自外层

    return round_it


r2 = make_rounder(2)
r0 = make_rounder(0)
r4 = make_rounder(4)

print("  r2(3.14159) ->", r2(3.14159))
print("  r0(3.14159) ->", r0(3.14159))
print("  r4(3.14159) ->", r4(3.14159))
print()
print("  没有闭包的话，你得写三个函数，或者每次调用都多传一个参数：")
print("    round(3.14159, 2) / round(x, 2) / round(y, 2) ...")
print("  闭包的意义：把「每个调用点都会重复的那个参数」提前绑死。")

print()
print("  更实际的用法 —— 传给排序：")
rows = [{"name": "b", "size": 30}, {"name": "a", "size": 10}]
by_size = lambda row: row["size"]  # noqa: E731
print("   sorted(rows, key=by_size) 已经够简单了，")
print("   但如果排序规则本身要参数（比如「按第几列排」），闭包就是唯一答案：")

def sort_by_column(index: int):
    return lambda row: row[index]

table = [("x", 3), ("y", 1), ("z", 2)]
print("    第 0 列:", sorted(table, key=sort_by_column(0)))
print("    第 1 列:", sorted(table, key=sort_by_column(1)))

print()
print("=" * 58)
print("② 装饰器：定义即注册（Flask 路由就是这个原理）")
print("=" * 58)

HANDLERS: dict[str, object] = {}


def register(action: str):
    def decorator(func):
        HANDLERS[action] = func  # ← 关键：在「定义函数的那一刻」就登记
        return func

    return decorator


@register("move")
def handle_move(path: str) -> str:
    return f"移动 {path}"


@register("copy")
def handle_copy(path: str) -> str:
    return f"复制 {path}"


print("  我只写了两个函数，从没手动维护过 HANDLERS：")
print("    HANDLERS 里有:", list(HANDLERS))

print()
print("  现在新增一个，注意我不需要改任何「注册表」：")
print()

# 假装这是后来同事加的功能
@register("delete")
def handle_delete(path: str) -> str:
    return f"删除 {path}"


print("    HANDLERS 里有:", list(HANDLERS))
print()
print("  手动注册的版本长这样，新增时必须记得改第二处：")
print('    def handle_delete(...): ...')
print('    HANDLERS = {"move": ..., "copy": ..., "delete": handle_delete}  ← 忘了就静默失效')

print()
print("  用名字分发：")
for action in ["move", "delete"]:
    handler = HANDLERS[action]
    print(f"    {action:8} -> {handler('/tmp/a.txt')}")  # type: ignore[operator]

print()
print("=" * 58)
print("③ 装饰器：消掉「每个函数都要写一遍」的杂事")
print("=" * 58)


def timed(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        cost = (time.perf_counter() - start) * 1000
        print(f"    [{func.__name__}] 耗时 {cost:.2f} ms")
        return result

    return wrapper


# 不加装饰器：每个函数都要重复这四行
def step_a() -> None:
    start = time.perf_counter()
    sum(range(200_000))
    print(f"    [step_a] 耗时 {(time.perf_counter() - start) * 1000:.2f} ms")


def step_b() -> None:
    start = time.perf_counter()
    sum(range(400_000))
    print(f"    [step_b] 耗时 {(time.perf_counter() - start) * 1000:.2f} ms")


print("  不加装饰器 —— 计时代码和业务代码混在一起：")
step_a()
step_b()


@timed
def step_c() -> None:
    sum(range(600_000))


@timed
def step_d() -> None:
    sum(range(800_000))


print()
print("  加装饰器 —— 函数体里只有业务本身：")
step_c()
step_d()

print()
print("  差别不在「少写几行」，在于：")
print("    1. 改计时方式时改一处，不用改十个函数")
print("    2. 看函数体时不会被杂事打断")
print("    3. 想临时关掉计时，注释掉 @timed 那一行就行")
