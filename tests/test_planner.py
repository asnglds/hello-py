"""plan / pick_destination 的测试。

和 test_rules.py 的区别：这里真的要造目录、放文件。
靠 tmp_path fixture —— 每个测试一个独立的空目录，跑完自动清理。
"""

import os
from pathlib import Path

import pytest

from orgtool.planner import pick_destination, plan
from orgtool.rules import RuleSet

RULES = RuleSet({".jpg": "images", ".pdf": "docs"})


def touch(folder: Path, *names: str, content: str = "x") -> None:
    """在 folder 下造几个文件。只是辅助函数，名字不以 test_ 开头。"""
    for name in names:
        (folder / name).write_text(content, encoding="utf-8")


# ---------- 基本映射 ----------


def test_maps_file_to_subfolder(tmp_path: Path) -> None:
    touch(tmp_path, "a.jpg")

    moves = list(plan(tmp_path, RULES))

    assert len(moves) == 1
    assert moves[0].src == tmp_path / "a.jpg"
    assert moves[0].dst == tmp_path / "images" / "a.jpg"


def test_unknown_extension_goes_to_others(tmp_path: Path) -> None:
    touch(tmp_path, "a.xyz")

    moves = list(plan(tmp_path, RULES))

    assert moves[0].dst.parent.name == "others"


# ---------- 过滤规则 ----------


def test_skips_hidden_files(tmp_path: Path) -> None:
    touch(tmp_path, ".keepme", "a.jpg")

    moves = list(plan(tmp_path, RULES))

    assert [m.src.name for m in moves] == ["a.jpg"]


def test_skips_subdirectories(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    touch(tmp_path, "a.jpg")

    moves = list(plan(tmp_path, RULES))

    assert [m.src.name for m in moves] == ["a.jpg"]


def test_empty_folder_yields_nothing(tmp_path: Path) -> None:
    assert list(plan(tmp_path, RULES)) == []


# ---------- 重名处理 ----------


def test_existing_target_gets_suffix(tmp_path: Path) -> None:
    """目标位置已有同名文件时，不能覆盖，要加 _1。"""
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "a.jpg").write_text("old", encoding="utf-8")
    touch(tmp_path, "a.jpg", content="new")

    moves = list(plan(tmp_path, RULES))

    assert moves[0].dst.name == "a_1.jpg"
    # 原来那个文件还在，内容没被碰
    assert (tmp_path / "images" / "a.jpg").read_text(encoding="utf-8") == "old"


@pytest.mark.skipif(
    os.name != "nt",
    reason="只在大小写不敏感的文件系统上成立；Linux 上两个文件可以并存",
)
def test_windows_filesystem_cannot_hold_case_only_twins(tmp_path: Path) -> None:
    """这条测试记录的是一个平台事实，不是我们的代码行为。

    Windows 文件系统不区分大小写，所以「同目录下 photo1.JPG 和 photo1.jpg 并存」
    这个场景**造不出来**：第二次写入改的是同一个文件。

    写下来是因为它影响你怎么读别的测试——
    凡是依赖「两个只差大小写的文件同时存在」的用例，在 Windows 上都跑不了。
    真正跨平台的写法是 atexit 清理 + os.name 判断，对现在这个项目属于过度设计。
    """
    touch(tmp_path, "photo1.JPG")
    touch(tmp_path, "photo1.jpg")

    assert len(list(tmp_path.iterdir())) == 1


def test_collision_inside_one_plan_is_detected(tmp_path: Path) -> None:
    """「计划内部撞车」：磁盘上什么都没有，但两个目标算出来是同一个路径。

    这里不靠真实文件复现（受上一条的平台限制影响），
    而是直接把「已被占用」的路径塞进 taken，验证 pick_destination 的机制本身。

    注意 taken 里用的是 **a.JPG**、跟目标同名同大小写：
    如果写成 a.jpg，这个用例就只在 Windows 上成立——
    Linux 区分大小写，a.JPG 和 a.jpg 不算撞车，断言会挂。
    测试也要能跨平台跑，CI 的两个平台才不会一个绿一个红。
    """
    taken = {os.path.normcase(tmp_path / "images" / "a.JPG")}

    dst = pick_destination(tmp_path, "images", "a.JPG", taken)

    assert dst.name == "a_1.JPG"


def test_pick_destination_avoids_every_taken_path(tmp_path: Path) -> None:
    """直接测 pick_destination：连续要三次路径，应该拿到三个不同的名字。"""
    taken: set[str] = set()

    first = pick_destination(tmp_path, "images", "a.jpg", taken)
    second = pick_destination(tmp_path, "images", "a.jpg", taken)
    third = pick_destination(tmp_path, "images", "a.jpg", taken)

    assert [p.name for p in (first, second, third)] == ["a.jpg", "a_1.jpg", "a_2.jpg"]


# ---------- 不变量：只算不做 ----------


def test_plan_does_not_touch_disk(tmp_path: Path) -> None:
    """plan() 的契约是「只计算」。这条测试就是用来守这个契约的。

    如果哪天有人手滑在 plan() 里加了 mkdir 或 move，这条会立刻变红。
    """
    touch(tmp_path, "a.jpg")

    list(plan(tmp_path, RULES))  # 把生成器跑完

    assert (tmp_path / "a.jpg").exists()  # 源文件还在原地
    assert not (tmp_path / "images").exists()  # 目标目录没被创建


# ---------- 生成器的两个特性 ----------


def test_generator_can_only_be_consumed_once(tmp_path: Path) -> None:
    """plan() 返回生成器，遍历一次就空了——这是契约的一部分，测试把它写下来。"""
    touch(tmp_path, "a.jpg")
    moves = plan(tmp_path, RULES)

    assert len(list(moves)) == 1
    assert list(moves) == []  # 第二次是空的，不是 bug


def test_generator_has_no_len(tmp_path: Path) -> None:
    """顺手把「不能 len」也固定下来。

    这里必须写 type: ignore —— pyright 知道 Iterator 没有 __len__，
    但这条测试的目的恰恰是「验证它确实没有」。这是 ignore 的正当用法：
    不是掩盖类型错误，而是主动依赖那个「错误」。
    """
    moves = plan(tmp_path, RULES)

    with pytest.raises(TypeError):
        len(moves)  # type: ignore[arg-type]
