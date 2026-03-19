"""主入口：加载配置、抓取、总结、保存"""

import os
from pathlib import Path

import yaml

from src.fetchers import fetch_rss, fetch_email, fetch_follow_builders_x, fetch_follow_builders_podcasts, fetch_youtube_transcript, RawItem
from src.summarize import summarize


def load_config(config_path: str = "sources.yaml") -> dict:
    """加载 sources.yaml，返回完整配置（含顶层 language 等字段）"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"请创建 {config_path}，可参考 sources.example.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_sources(config_path: str = "sources.yaml") -> list[dict]:
    """加载 sources.yaml（向后兼容）"""
    return load_config(config_path).get("sources", [])


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

        elif stype == "follow_builders_x":
            items.extend(fetch_follow_builders_x(
                max_tweets_per_person=src.get("max_tweets_per_person", 3)
            ))

        elif stype == "follow_builders_podcasts":
            items.extend(fetch_follow_builders_podcasts(
                max_episodes=src.get("max_episodes", 3),
                transcript_chars=src.get("transcript_chars", 2000),
            ))

        elif stype == "youtube_transcript":
            items.extend(fetch_youtube_transcript(
                source_name=name,
                channel_handle=src.get("channel_handle"),
                playlist_id=src.get("playlist_id"),
                lookback_hours=src.get("lookback_hours", 72),
            ))

    return items


def run(config_path: str = "sources.yaml", output_dir: str = "summaries", api_key: str | None = None) -> str:
    """完整流程：抓取 → 总结 → 保存"""
    from datetime import datetime

    config = load_config(config_path)
    sources = config.get("sources", [])
    language = config.get("language", "zh")  # zh | en | bilingual

    items = fetch_all(sources)
    summary_text = summarize(items, api_key=api_key, language=language)

    # 保存到文件
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = Path(output_dir) / f"{today}.md"

    title_map = {"zh": "每日摘要", "en": "Daily Summary", "bilingual": "每日摘要 / Daily Summary"}
    title = title_map.get(language, "每日摘要")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {title} {today}\n\n")
        f.write(summary_text)
    return str(out_path)


if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("请设置环境变量 ANTHROPIC_API_KEY")
        exit(1)

    out = run(api_key=api_key)
    print(f"摘要已保存到: {out}")
