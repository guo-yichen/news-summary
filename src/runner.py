"""主入口：加载配置、抓取、总结、保存"""

import os
from pathlib import Path

import yaml

from src.fetchers import (
    fetch_rss, fetch_email, fetch_gmail,
    fetch_youtube, fetch_youtube_transcript,
    fetch_twitter,
    fetch_follow_builders_x, fetch_follow_builders_podcasts,
    RawItem,
)
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

        elif stype == "youtube":
            url = src.get("url")
            if not url:
                items.append(RawItem(source_name=name, source_type="youtube", title="[配置错误]", content="缺少 url", link=None))
                continue
            items.extend(fetch_youtube(url, name,
                max_entries=src.get("max_entries", 3),
                languages=src.get("languages", ["zh-Hans", "zh", "en"]),
            ))

        elif stype == "twitter":
            cookies_path = src.get("cookies_path") or os.environ.get("TWITTER_COOKIES_PATH", "twitter_cookies.json")
            items.extend(fetch_twitter(
                cookies_path=cookies_path,
                source_name=name,
                usernames=src.get("usernames", []),
                max_tweets=src.get("max_tweets", 20),
            ))

        elif stype == "gmail":
            items.extend(fetch_gmail(
                source_name=name,
                credentials_json=src.get("credentials_json"),
                query=src.get("query", "is:unread"),
                max_emails=src.get("max_emails", 5),
            ))

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
    """完整流程：抓取 → 总结 → 保存（Notion 或 Markdown）"""
    from datetime import datetime

    config = load_config(config_path)
    sources = config.get("sources", [])
    language = config.get("language", "zh")  # zh | en | bilingual

    items = fetch_all(sources)
    print(f"共抓取 {len(items)} 条内容")

    summary_text = summarize(items, api_key=api_key, language=language)

    output_mode = os.environ.get("OUTPUT_MODE", "markdown")  # notion | markdown | both
    today = datetime.now().strftime("%Y-%m-%d")
    results = []

    if output_mode in ("markdown", "both"):
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        out_path = Path(output_dir) / f"{today}.md"
        title_map = {"zh": "每日摘要", "en": "Daily Summary", "bilingual": "每日摘要 / Daily Summary"}
        title = title_map.get(language, "每日摘要")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {title} {today}\n\n")
            f.write(summary_text)
        results.append(f"Markdown: {out_path}")

    if output_mode in ("notion", "both"):
        from src.notion_writer import write_to_notion
        try:
            notion_url = write_to_notion(summary_text)
            results.append(f"Notion: {notion_url}")
        except Exception as e:
            print(f"Notion 写入失败: {e}")
            if output_mode == "notion":  # fallback
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                out_path = Path(output_dir) / f"{today}.md"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(summary_text)
                results.append(f"Markdown (fallback): {out_path}")

    return "\n".join(results)


if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("请设置环境变量 ANTHROPIC_API_KEY")
        exit(1)

    out = run(api_key=api_key)
    print(f"完成！\n{out}")
