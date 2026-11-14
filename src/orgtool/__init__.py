"""orgtool · 按扩展名归档文件的小工具。

这个文件（包的 __init__）只做一件事：把稳定的公共接口摆出来。

注意这里**不导入 cli**。因为 cli 会拉进 argparse、shutil 这些模块，
而别人想用 `from orgtool import RuleSet` 时，不该被迫加载整套命令行工具。
「导入代价」也是接口设计的一部分。
"""

from .models import Move
from .planner import pick_destination, plan
from .rules import RuleError, RuleSet

__all__ = ["Move", "RuleError", "RuleSet", "pick_destination", "plan"]
__version__ = "0.1.0"
