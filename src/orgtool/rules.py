"""规则：扩展名 -> 目标目录 的映射，以及加载它的入口。

这个模块只依赖标准库，不依赖项目内其他模块。
「只依赖更底层的东西」是模块划分的一条硬规矩——
如果 rules.py 反过来 import planner，两个文件就缠在一起了，谁也没法单独用。
"""

import json
from pathlib import Path


class RuleError(Exception):
    """规则文件相关的问题：读不了、不是合法 JSON、内容不合规。

    自定义异常类型的目的不是「显得专业」，是让调用方可以精确捕获：
    如果这里抛 ValueError，调用方写 except ValueError 时，
    会把自己代码里其他地方的 ValueError 一起吞掉，bug 就被掩盖了。
    """


class RuleSet:
    """扩展名 -> 目标目录 的映射表，从 JSON 文件加载。

    为什么用普通类而不是 dataclass：
    dataclass 适合「纯数据」，字段是什么、存什么，一眼看完。
    这个类有行为（加载、查表、算属性），而且要在 __init__ 里把键统一转小写，
    用普通类写反而更直接。
    """

    def __init__(self, mapping: dict[str, str]) -> None:
        # 键统一转小写，这样 .JPG 和 .jpg 都能查到。
        # 「统一在入口处归一化」——和 cli 里 str 转 Path 是同一个思路。
        self._mapping = {k.lower(): v for k, v in mapping.items()}

    @classmethod
    def from_json(cls, path: Path) -> "RuleSet":
        """从 JSON 文件读规则。

        为什么不写在 __init__ 里：__init__ 应该只收「已经解析好的数据」。
        读文件可能失败（不存在、格式错），把它放在独立的构造入口里，
        调用方就能明确知道「这一步可能抛异常」，而不是每次造对象都提心吊胆。

        所有失败都转成 RuleError，并用 from 挂上原始异常——
        这样报错信息里有文件名和行列号，排查时不用猜是哪个文件。
        """
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RuleError(f"读不了规则文件：{path}") from exc

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuleError(
                f"规则文件不是合法 JSON：{path}（第 {exc.lineno} 行第 {exc.colno} 列：{exc.msg}）"
            ) from exc

        if not isinstance(raw, dict):
            raise RuleError(f"规则文件应该是一个 JSON 对象，实际是 {type(raw).__name__}：{path}")
        for ext, folder in raw.items():
            if not ext.startswith("."):
                raise RuleError(f"扩展名必须以点开头：{ext!r}（在 {path}）")
            if not isinstance(folder, str):
                raise RuleError(f"目录名必须是字符串：{ext} -> {folder!r}")
        return cls(raw)

    @property
    def extensions(self) -> tuple[str, ...]:
        """所有支持的扩展名，排序后返回。每次读都现算，所以和 _mapping 永远一致。"""
        return tuple(sorted(self._mapping))

    @property
    def folders(self) -> tuple[str, ...]:
        """所有目标目录名，去重且排序。"""
        return tuple(sorted(set(self._mapping.values())))

    def folder_for(self, path: Path) -> str:
        """给一个文件，返回它该去的子目录名；不认识的扩展名归到 others。"""
        return self._mapping.get(path.suffix.lower(), "others")
