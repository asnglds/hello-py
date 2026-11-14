# orgtool

按扩展名把文件归档到子目录的命令行工具。

几条刻意的设计：

- **先算再做**：`--dry-run` 只打印计划，确认之后才真的移动
- **不覆盖**：目标位置已有同名文件时自动加 `_1`、`_2` 序号
- **不中断**：单个文件失败（被占用、没权限）不影响其余文件，最后统一汇报
- **可重入**：重复运行不会出问题，第二次会告诉你「没有需要整理的文件」
- **规则外置**：扩展名映射在 `rules.json` 里，改规则不用改代码

## 安装

```bash
# 在项目目录里，装进虚拟环境（开发用）
uv sync

# 或者装成全局命令（日常用）
uv tool install .
```

## 用法

```bash
# 先看计划，不动任何文件
uv run orgtool "D:\Downloads" --dry-run

# 确认没问题，真的执行
uv run orgtool "D:\Downloads"

# 用另一套规则
uv run orgtool "D:\Downloads" --rules my-rules.json

# 看帮助
uv run orgtool --help
```

`folder` 是必填的。这个不是设计疏忽——早期版本默认整理当前目录，
结果有人在项目根目录直接运行，把项目自己的文件全搬走了。必填之后，
「忘了给参数」会被立刻拦住，而不是变成一次意外操作。

## 规则文件

默认使用包内自带的 `rules.json`（跟着 `orgtool` 一起安装）：

```json
{
  ".jpg": "images",
  ".png": "images",
  ".pdf": "docs",
  ".zip": "archives"
}
```

键必须是带点的扩展名，值必须是字符串。不认识的扩展名统一进 `others`。
规则文件写错时，报错会带上文件名和行列号，比如：

```
规则文件不是合法 JSON：rules.json（第 1 行第 9 列：Expecting property name enclosed in double quotes）
```

## 项目结构

```
src/orgtool/
├── __init__.py    导出公共接口
├── models.py      Move —— 一次搬移记录
├── rules.py       RuleSet / RuleError —— 规则加载与校验
├── planner.py     plan / pick_destination —— 算出搬移计划（不碰磁盘）
└── cli.py         命令行入口与执行
examples/          与工具无关的示例脚本
learn/             学习阶段留下的演示代码
```

依赖方向是单向的：`cli → planner → rules`，`planner` 和 `rules` 都只依赖 `models`。
没有一个箭头往回指，所以每一层都能单独导入、单独测试。

## 开发

```bash
uv run pytest        # 待补：阶段 2 模块 3
uv run ruff check .  # 待补：阶段 2 模块 2
uv run pyright       # 待补：阶段 2 模块 2
```
