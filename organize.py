"""按扩展名自动归档文件的小工具。

用法：
    uv run python organize.py "D:\\路径\\目标目录" --dry-run    只看计划
    uv run python organize.py "D:\\路径\\目标目录"              真的执行
"""

import argparse
import shutil
from pathlib import Path

# 扩展名 -> 目标子目录。
# 注意：左边必须是一个完整的扩展名字符串（带点），不能写成 ".md .csv"。
# 多个键可以指向同一个值，这才是"多对一"的正确表达。
FOLDERS = {
    ".jpg": "images",
    ".jpeg": "images",
    ".png": "images",
    ".gif": "images",
    ".pdf": "docs",
    ".txt": "docs",
    ".md": "docs",
    ".csv": "docs",
    ".mp4": "videos",
    ".mov": "videos",
    ".avi": "videos",
    ".zip": "archives",
    ".rar": "archives",
    ".7z": "archives",
}


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    folder 故意不设默认值。早期版本默认是 "."，
    结果有人在项目目录里直接跑，把项目自己的文件全搬走了。
    让参数必填，就少了一层"意外的默认行为"。
    """
    parser = argparse.ArgumentParser(description="按扩展名归档文件")
    parser.add_argument("folder", help="要整理的目录（必填）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不移动文件")
    return parser.parse_args()


def pick_destination(folder: Path, target_dir: str, name: str, taken: set[str]) -> Path:
    """算出目标路径；重名时追加 _1、_2 序号，绝不覆盖已有文件。

    taken 记录本次计划里已经分配出去的路径。
    为什么需要它：只看 dst.exists() 会漏掉"计划内部撞车"的情况——
    比如 photo1.jpg 和 photo1.JPG 都映射到 images/，
    而 Windows 文件名不区分大小写，它们其实是同一个路径。
    """
    stem = Path(name).stem      # 主名，如 photo1
    suffix = Path(name).suffix  # 扩展名，如 .JPG

    dst = folder / target_dir / name
    n = 1
    # 用「小写后的路径字符串」当 key，因为 Windows 文件名不区分大小写，
    # Path 对象直接比较是区分大小写的，会漏掉 Photo.jpg 和 photo.jpg 这种冲突
    while dst.exists() or dst.as_posix().lower() in taken:
        dst = folder / target_dir / f"{stem}_{n}{suffix}"
        n += 1

    taken.add(dst.as_posix().lower())
    return dst


def plan(folder: Path) -> list[tuple[Path, Path]]:
    """先算出"每个文件该搬到哪"，只计算，不动手。

    把"想"和"做"分开有两个好处：
    1. 可以先打印给人看，再决定要不要真做（--dry-run）
    2. 遍历期间不创建目录、不移动文件，避免边遍历边改目录结构
    """
    result: list[tuple[Path, Path]] = []
    taken: set[str] = set()

    for item in folder.iterdir():
        # 跳过子目录，否则 images/ 这种也会被当成文件处理
        if not item.is_file():
            continue

        # 跳过隐藏文件：.gitignore、.gitattributes、.python-version 这类
        # 是配置而不是待归档的内容，动了会出事
        if item.name.startswith("."):
            continue

        ext = item.suffix.lower()               # .JPG 和 .jpg 视为同一种
        target_dir = FOLDERS.get(ext, "others")  # 查不到就用 others
        dst = pick_destination(folder, target_dir, item.name, taken)

        result.append((item, dst))

    return result


def main() -> None:
    args = parse_args()
    folder = Path(args.folder)

    # 先确认目录存在，否则后面 iterdir() 会抛出难懂的异常
    if not folder.is_dir():
        print(f"目录不存在：{folder}")
        return

    for src, dst in plan(folder):
        # 试运行：只打印，continue 直接跳到下一个文件
        if args.dry_run:
            print(f"[试运行] {src.name:<20} -> {dst.relative_to(folder)}")
            continue

        # 目标子目录可能还不存在，先建出来（已存在就当没发生）
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
        print(f"{src.name:<20} -> {dst.relative_to(folder)}")


if __name__ == "__main__":
    main()
