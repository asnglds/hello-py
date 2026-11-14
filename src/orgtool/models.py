"""数据模型：只描述「数据长什么样」，不放行为。

这个模块不导入任何项目内的其他模块——它是依赖链的最底层。
把数据模型单独放一个文件，好处是别人想知道「一条搬移记录有哪些字段」，
打开这一个文件就够了，不用在几百行里翻。
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Move:
    """一次搬移：从哪到哪。

    用 dataclass 而不是 tuple，唯一理由就是：字段有名字。
    tuple 写成 (src, dst) 时，三个月后看到 moves[3][1] 得靠记忆判断它是谁；
    move.dst 一眼就明白，拼错了 Pylance 还会立刻报红。

    frozen=True 让它不可变，顺带获得可哈希能力（能进 set、能当字典键）。
    """

    src: Path
    dst: Path
