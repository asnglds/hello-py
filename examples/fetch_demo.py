"""示例脚本：调用接口 → 解析 JSON → 写 CSV。

和 orgtool 没有关系，它只是阶段 0 的第一个练手脚本，留在这里当样例。

它用到了 requests，而 orgtool 本体只用标准库——
所以这个依赖被放进了 pyproject 的 dev 组，不是工具的运行依赖。
"""

import csv
from pathlib import Path

import requests


def fetch_slideshow() -> dict[str, object]:
    resp = requests.get("https://httpbin.org/json", timeout=10)
    resp.raise_for_status()
    return resp.json().get("slideshow", {})


def main() -> None:
    data = fetch_slideshow()
    rows = [{"key": k, "value": str(v)[:60]} for k, v in data.items()]

    out = Path("output.csv")
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["key", "value"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"写入 {len(rows)} 行 -> {out.resolve()}")


if __name__ == "__main__":
    main()
