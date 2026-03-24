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


def fetch_all(sources: list[dict], global_max_entries: int = 3, global_max_age_days: int = 30) -> list[RawItem]:
    """根据配置抓取所有源

    global_max_entries: 全局每源最多条数上限（sources.yaml 里的单独设置不超过此值）
    global_max_age_days: 全局文章最大年龄（天），超过此天数的文章跳过
    """
    items: list[RawItem] = []
    for src in sources:
        stype = src.get("type", "rss")
        name = src.get("name", "未命名")
        before = len(items)

        if stype == "rss":
            url = src.get("url")
            if not url:
                items.append(RawItem(source_name=name, source_type="rss", title="[配置错误]", content="缺少 url", link=None))
                continue
            items.extend(fetch_rss(
                url, name,
                max_entries=min(src.get("max_entries", 3), global_max_entries),
                fetch_fulltext=src.get("fetch_fulltext", False),
                fulltext_chars=src.get("fulltext_chars", 8000),
                max_age_days=src.get("max_age_days", global_max_age_days),
            ))

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
                transcript_chars=src.get("transcript_chars", 15000),
            ))

        elif stype == "youtube_transcript":
            items.extend(fetch_youtube_transcript(
                source_name=name,
                channel_handle=src.get("channel_handle"),
                playlist_id=src.get("playlist_id"),
                lookback_hours=src.get("lookback_hours", 72),
            ))

        # If this source added nothing new, insert a "no update" placeholder
        if len(items) == before and not (stype in ("email", "youtube", "twitter", "gmail") and not src.get("url")):
            items.append(RawItem(
                source_name=name,
                source_type=stype,
                title="暂无更新",
                content="该来源今日无新内容（已抓取但无符合条件的条目）",
                link=None,
            ))

    return items


def run(config_path: str = "sources.yaml", output_dir: str = "summaries", api_key: str | None = None) -> str:
    """完整流程：抓取 → 总结 → 保存（Notion 或 Markdown）"""
    from datetime import datetime

    config = load_config(config_path)
    sources = config.get("sources", [])
    language = config.get("language", "zh")  # zh | en | bilingual
    global_max_entries = config.get("max_entries", 3)
    global_max_age_days = config.get("max_age_days", 30)

    items = fetch_all(sources, global_max_entries=global_max_entries, global_max_age_days=global_max_age_days)
    print(f"共抓取 {len(items)} 条内容")

    # 过滤错误项，避免污染摘要
    valid_items = [i for i in items if not (i.title.startswith("[") and i.title.endswith("]"))]
    error_items = [i for i in items if i not in valid_items]
    if error_items:
        print(f"[警告] 跳过 {len(error_items)} 个抓取失败的条目: {[i.source_name for i in error_items]}")

    # 把"暂无更新"的条目排到末尾，使输出中有内容的来源优先显示
    valid_items.sort(key=lambda i: i.title == "暂无更新")

    summary_text = summarize(valid_items, api_key=api_key, language=language)

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

    # 推送到 Telegram
    tg_cfg = config.get("telegram", {})
    tg_token = tg_cfg.get("bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = tg_cfg.get("chat_id") or os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            from src.telegram_notifier import send_to_telegram
            n_msgs = send_to_telegram(summary_text, bot_token=tg_token, chat_id=str(tg_chat), date=today)
            print(f"Telegram 已发送 {n_msgs} 条消息")
            results.append(f"Telegram: {n_msgs} 条消息")
        except Exception as e:
            print(f"[警告] Telegram 推送失败: {e}")

    # 发送邮件
    email_user = os.environ.get("EMAIL_USER")
    email_password = os.environ.get("EMAIL_PASSWORD")
    email_to = os.environ.get("EMAIL_TO") or email_user
    if email_user and email_password:
        try:
            from src.email_sender import send_email
            send_email(summary_text, date=today, smtp_user=email_user,
                       smtp_password=email_password, to_address=email_to, language=language)
            print(f"邮件已发送至 {email_to}")
            results.append(f"Email: {email_to}")
        except Exception as e:
            print(f"[警告] 邮件发送失败: {e}")

    return "\n".join(results)


if __name__ == "__main__":
    api_key = os.environ.get("KIMI_API_KEY")
    if not api_key:
        print("请设置环境变量 KIMI_API_KEY")
        exit(1)

    out = run(api_key=api_key)
    print(f"完成！\n{out}")
