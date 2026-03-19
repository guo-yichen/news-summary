"""RSS 抓取：支持 Substack、博客、YouTube、播客、Twitter(Nitter/OpenRSS)"""

import re
import feedparser
from .base import RawItem
from src import state as _state


def fetch_rss(url: str, source_name: str, max_entries: int = 3) -> list[RawItem]:
    """抓取 RSS feed，返回 RawItem 列表（跨天自动去重，7 天内不重复推送同一篇文章）"""
    items: list[RawItem] = []
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": "NewsSummary/1.0"})
    except Exception as e:
        return [RawItem(source_name=source_name, source_type="rss", title="[抓取失败]", content=str(e), link=url)]

    st = _state.load()
    new_items = []

    for entry in feed.entries:
        if len(new_items) >= max_entries:
            break

        title = entry.get("title", "(无标题)")
        summary = entry.get("summary", entry.get("description", ""))
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", ""))

        # 用链接去重；无链接的文章不去重
        if link and _state.is_seen(st, "seenArticles", link):
            continue

        # 清理 HTML 标签
        if summary and "<" in summary:
            summary = re.sub(r"<[^>]+>", " ", summary)
            summary = " ".join(summary.split())

        if link:
            _state.mark_seen(st, "seenArticles", link)

        new_items.append(RawItem(
            source_name=source_name,
            source_type="rss",
            title=title,
            content=summary or title,
            link=link,
            published=published,
        ))

    _state.save(st)
    return new_items
