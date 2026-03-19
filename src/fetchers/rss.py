"""RSS 抓取：支持 Substack、博客、YouTube、播客、Twitter(Nitter/OpenRSS)"""

import feedparser
from .base import RawItem


def fetch_rss(url: str, source_name: str, max_entries: int = 3) -> list[RawItem]:
    """抓取 RSS feed，返回 RawItem 列表"""
    items: list[RawItem] = []
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": "NewsSummary/1.0"})
    except Exception as e:
        return [RawItem(source_name=source_name, source_type="rss", title="[抓取失败]", content=str(e), link=url)]

    for entry in feed.entries[:max_entries]:
        title = entry.get("title", "(无标题)")
        summary = entry.get("summary", entry.get("description", ""))
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", ""))

        # 清理 HTML 标签（简单处理）
        if summary and "<" in summary:
            import re
            summary = re.sub(r"<[^>]+>", " ", summary)
            summary = " ".join(summary.split())

        items.append(
            RawItem(
                source_name=source_name,
                source_type="rss",
                title=title,
                content=summary or title,
                link=link,
                published=published,
            )
        )

    return items
