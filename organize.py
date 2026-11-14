"""兼容入口。

真正的代码已经搬进 src/orgtool/，这里只剩两行转发。

为什么还留着它：你之前所有的命令、笔记、肌肉记忆都是
`uv run python organize.py ...`。保留这个文件，让旧命令继续能用，
就不用为了拆包去改一堆已经写好的东西。

等某个时刻你发现再也没用过它，删掉就行。
"""

from orgtool.cli import main

if __name__ == "__main__":
    main()
