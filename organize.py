import argparse
import shutil
from pathlib import Path

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


def plan(folder: Path) -> list[tuple[Path, Path]]:
    result = []
    for item in folder.iterdir():
        if not item.is_file():
            continue
        ext = item.suffix.lower()
        target_dir = FOLDERS.get(ext, "others")
        result.append((item, folder / target_dir / item.name))
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按扩展名归档文件")
    parser.add_argument("folder", nargs="?", default=".", help="要整理的目录")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不移动")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    folder = Path(args.folder)

    for src, dst in plan(folder):
        if args.dry_run:
            print(f"[试运行] {src.name:<20} -> {dst.parent.name}/")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
        print(f"{src.name:<20} -> {dst.parent.name}/")


if __name__ == "__main__":
    main()
