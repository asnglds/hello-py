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

# 看每个文件为什么去那儿（DEBUG 级别，输出决策过程）
uv run orgtool "D:\Downloads" --dry-run -v

# 屏幕上只留错误，完整细节（含 DEBUG 和 traceback）写进文件
uv run orgtool "D:\Downloads" -q --log-file run.log

# 看帮助
uv run orgtool --help
```

`-v` 和 `-q` 互斥，同时给会被 argparse 直接拒绝。

日志默认写 **stderr**，所以 `orgtool ... > result.txt` 得到的文件是空的——
这是有意的，日志是过程不是数据。想留下日志请用 `--log-file` 或 `2> run.log`。

`folder` 是必填的。这个不是设计疏忽——早期版本默认整理当前目录，
结果有人在项目根目录直接运行，把项目自己的文件全搬走了。必填之后，
「忘了给参数」会被立刻拦住，而不是变成一次意外操作。

## 性能：为什么不并发

整理 1000 个文件（17 种扩展名混合，其中 200 个目标位置已有同名文件），本机实测：

| 阶段 | 耗时 | 占比 |
|---|---|---|
| 规划（算出每个文件该去哪，不碰磁盘） | 0.15 s | 35% |
| 移动（真的搬） | 0.29 s | 65% |
| **合计** | **0.44 s** | |

规划阶段再优化也没意义——全部省掉只快 0.15 秒。成本在搬的那一步。

### 试过线程池，结果是灾难

| 线程数 | 耗时 | 相对串行 |
|---|---|---|
| 1（串行） | 0.39 s | 1.00x |
| 2 | 2.34 s | 0.17x |
| 4 | **18.07 s** | **0.02x** |
| 8 | 23.56 s | 0.02x |
| 16 | 18.89 s | 0.02x |

4 个线程就慢了 46 倍。而且把 `mkdir` 和 `shutil.move` 全剥掉、只留纯 `os.rename`，
表现一模一样——**所以不是代码写得不对，是这台机器上多线程做元数据写操作会退化成排队。**

已经排除的原因：杀软实时扫描（全程关闭）、第三方安全软件（无注册项）、
磁盘故障（NTFS 卷健康）、BitLocker（未启用）。
没查清的：NTFS 8.3 短名生成的卷级锁（需要管理员权限，`fsutil 8dot3name query D:`）。

**结论：默认串行。** 并发代码留在 `cli.run_concurrent` 里，用 `--workers N` 显式开启，
只建议拿来做实验——它在本机比串行慢一个数量级。

### 真正有效的优化

| 改动 | 效果 |
|---|---|
| 用 `os.rename` 替代 `shutil.move` | 移动阶段 0.392 → 0.286 s（−27%） |

`shutil.move` 每次都要额外做一次 `os.path.isdir(dst)` 和审计钩子调用，
而目标文件不存在这件事由 `pick_destination` 已经保证了。同盘直接用 `os.rename`，
只在跨盘（`errno.EXDEV`）时才退回 `shutil.move`。

这个数字比"加并发"好看得多，而且没有引入任何复杂度。

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
uv run pytest            # 23 个用例
uv run ruff check .      # lint + import 排序
uv run ruff format --check .
uv run pyright           # standard 档，0 错误
uv run pre-commit run --all-files   # 三个钩子一次跑完
```

提交时 pre-commit 会自动跑 ruff 两个钩子（只处理本次改动的文件，毫秒级）。
pyright 是 manual stage——提交钩子只放秒级检查，全量类型分析属于 CI 的活。

基准脚本在 `examples/`，用来复现上面的数字：

```bash
uv run python examples/bench_serial.py    # 串行基线
uv run python examples/bench_thread.py    # 线程池版（会看到它多慢）
uv run python examples/bench_workers.py   # 1/2/4/8/16 线程曲线
uv run python examples/bench_meta.py      # 短名 vs 长名，验证 8.3 短名的影响
```

⚠️ 基准必须在自己机器的终端里跑。在带文件安全沙箱的环境（比如某些 IDE 的
内置终端代理）里测，每个写操作会平白多出 4 毫秒，数字完全失真。
