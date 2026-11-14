"""RuleSet 的测试。

pytest 只认两条规矩：
    1. 文件名要叫 test_*.py（或 *_test.py）
    2. 函数名要以 test_ 开头

除此之外没有任何要求：不用继承类、不用 assertEqual、不用把测试放进 class。
`assert x == y` 就够了——pytest 会在失败时把 x 和 y 的值都打印出来。
"""

import json
from pathlib import Path

import pytest

from orgtool.rules import RuleError, RuleSet


def write_rules(tmp_path: Path, data: object) -> Path:
    """把任意数据写成 JSON 文件。不是测试函数，名字不以 test_ 开头，pytest 会跳过它。

    这类「测试用的小工具」不需要 fixture，一个普通函数就够。
    等它需要在每个测试里都重新准备时，再升级成 fixture。
    """
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


# ---------- 查表：正常路径 ----------


def test_folder_for_returns_target() -> None:
    rules = RuleSet({".jpg": "images"})
    assert rules.folder_for(Path("a.jpg")) == "images"


def test_unknown_extension_falls_back_to_others() -> None:
    rules = RuleSet({".jpg": "images"})
    assert rules.folder_for(Path("a.xyz")) == "others"


def test_file_without_extension_falls_back_to_others() -> None:
    rules = RuleSet({".jpg": "images"})
    assert rules.folder_for(Path("noext")) == "others"


# ---------- 不变量的守住 ----------
# 「不变量」= 这个类无论如何都要成立的性质。
# 下面两条就是 RuleSet 的不变量：键永远小写、folders 永远去重且有序。


def test_keys_are_normalized_to_lowercase() -> None:
    rules = RuleSet({".JPG": "images"})
    assert rules.folder_for(Path("a.jpg")) == "images"
    assert rules.folder_for(Path("a.JPG")) == "images"


def test_folders_are_unique_and_sorted() -> None:
    rules = RuleSet({".png": "images", ".jpg": "images", ".pdf": "docs"})
    assert rules.folders == ("docs", "images")


# ---------- 错误路径 ----------
# 参数化：同一个测试跑三组数据。失败时会分别报告是哪一组挂的。


@pytest.mark.parametrize(
    "bad_content",
    [
        {"jpg": "images"},  # 扩展名没带点
        {".jpg": 1},  # 值不是字符串
        ["not", "a", "dict"],  # 顶层不是对象
    ],
    ids=["no-dot", "value-not-str", "not-a-dict"],
)
def test_invalid_content_raises_rule_error(tmp_path: Path, bad_content: object) -> None:
    path = write_rules(tmp_path, bad_content)
    with pytest.raises(RuleError):
        RuleSet.from_json(path)


def test_broken_json_reports_position(tmp_path: Path) -> None:
    """语法错时，消息里要带行列号——这是排查时唯一有用的信息。"""
    path = tmp_path / "rules.json"
    path.write_text('{"a": 1,,}', encoding="utf-8")

    with pytest.raises(RuleError, match="第 1 行"):
        RuleSet.from_json(path)


def test_missing_file_raises_rule_error(tmp_path: Path) -> None:
    with pytest.raises(RuleError, match="读不了"):
        RuleSet.from_json(tmp_path / "nope.json")


# ---------- 正常加载 ----------


def test_from_json_loads_real_file(tmp_path: Path) -> None:
    path = write_rules(tmp_path, {".jpg": "images", ".pdf": "docs"})
    rules = RuleSet.from_json(path)

    assert rules.folder_for(Path("x.jpg")) == "images"
    assert rules.extensions == (".jpg", ".pdf")
