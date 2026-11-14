"""模块 6 补充 · raise ... from 异常链。

要看清三件事：
    1. 不包装异常，调用方拿到的是什么
    2. raise X from exc 之后，报错长什么样
    3. from None 什么时候用
"""

import json
import traceback
from pathlib import Path

TMP = Path("learn/_tmp_bad.json")
TMP.write_text('{"a": 1,,}', encoding="utf-8")  # 故意写坏

print("=" * 60)
print("① 不包装：底层异常直接漏给调用方")
print("=" * 60)


def load_plain(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


try:
    load_plain(TMP)
except Exception as exc:
    print("  调用方 catch 到的类型:", type(exc).__name__)
    print("  消息:", exc)
    print()
    print("  问题：这条消息里没有任何「是哪个文件出错了」的线索。")
    print("  如果同时读三个配置文件，你根本不知道是哪一个。")

print()
print("=" * 60)
print("② 包装 + from：把底层异常变成自己的，并保留原因")
print("=" * 60)


class ConfigError(Exception):
    """配置相关的错误。调用方只需要 catch 这一个类型。"""


def load_wrapped(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"读不了配置文件：{path}") from exc

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"配置文件不是合法 JSON：{path}（第 {exc.lineno} 行第 {exc.colno} 列）") from exc


try:
    load_wrapped(TMP)
except ConfigError as exc:
    print("  调用方 catch 到的类型:", type(exc).__name__)
    print("  消息:", exc)
    print()
    print("  traceback（只看最后几行）：")
    for line in traceback.format_exc().splitlines()[-6:]:
        print("   ", line)

print()
print("  「direct cause」那一段是 from 加上去的：")
print("  它的意思是「这个错误是由下面那个引起的」，两个都保留。")

print()
print("=" * 60)
print("③ from None：切断因果，只给结论")
print("=" * 60)


def load_quiet(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ConfigError(f"配置文件有问题：{path}") from None


try:
    load_quiet(TMP)
except ConfigError:
    print("  traceback（对比上面，没有 cause 那一段了）：")
    for line in traceback.format_exc().splitlines()[-5:]:
        print("   ", line)

print()
print("  什么时候用 from None：底层细节不该暴露给使用者时。")
print("  比如给最终用户的命令行工具——他不需要知道 JSONDecodeError 是什么。")

print()
print("=" * 60)
print("④ 三种写法的区别")
print("=" * 60)
print("  raise X            → 因果链自动挂上（Python 会记 __context__）")
print("  raise X from exc   → 显式声明「exc 是原因」，traceback 显示 direct cause")
print("  raise X from None  → 明确切断，不在 traceback 里显示底层异常")
print()
print("  推荐：只要你在 except 块里抛新异常，就写 from。")
print("  写 from exc 保留线索，写 from None 表达「我故意不告诉你」。")

TMP.unlink(missing_ok=True)
