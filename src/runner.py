"""主入口：加载配置、抓取、总结、保存"""

import os
from pathlib import Path

import yaml

from src.fetchers import fetch_rss, fetch_email, RawItem
from src.summarize import summarize


def load_sources(config_path: str = "sources.yaml") -> list[dict]:
    """加载 sources.yaml"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"请创建 {config_path}，可参考 sources.example.yaml")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


def fetch_all(sources: list[dict]) -> list[RawItem]:
    """根据配置抓取所有源"""
    items: list[RawItem] = []
    for src in sources:
        stype = src.get("type", "rss")
        name = src.get("name", "未命名")

        if stype == "rss":
            url = src.get("url")
            if not url:
                items.append(RawItem(source_name=name, source_type="rss", title="[配置错误]", content="缺少 url", link=None))
                continue
            max_entries = src.get("max_entries", 3)
            items.extend(fetch_rss(url, name, max_entries))

        elif stype == "email":
            if not all(src.get(k) for k in ("imap_server", "email", "password")):
                items.append(RawItem(source_name=name, source_type="email", title="[配置错误]", content="缺少 imap_server/email/password", link=None))
                continue
            items.extend(
                fetch_email(
                    imap_server=src["imap_server"],
                    email=src["email"],
                    password=src["password"],
                    source_name=name,
                    folder=src.get("folder", "INBOX"),
                    search_from=src.get("search_from"),
                    max_emails=src.get("max_emails", 5),
                )
            )

    return items


def run(config_path: str = "sources.yaml", output_dir: str = "summaries", api_key: str | None = None) -> str:
    """完整流程：抓取 → 总结 → 保存"""
    from datetime import datetime

    sources = load_sources(config_path)
    items = fetch_all(sources)

    summary_text = summarize(items, api_key=api_key)

    # 保存到文件
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = Path(output_dir) / f"{today}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# 每日摘要 {today}\n\n")
        f.write(summary_text)
    return str(out_path)


if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("请设置环境变量 ANTHROPIC_API_KEY")
        exit(1)

    out = run(api_key=api_key)
    print(f"摘要已保存到: {out}")
