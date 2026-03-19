"""RSS 抓取：支持 Substack、博客、YouTube、播客、Twitter(Nitter/OpenRSS)"""

import re
import feedparser
from .base import RawItem
from src import state as _state


def _fetch_fulltext(url: str, max_chars: int = 8000) -> str | None:
    """用 trafilatura 抓取文章正文，失败时返回 None"""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        if text and len(text) > max_chars:
            text = text[:max_chars] + "…（正文已截断）"
        return text
    except Exception:
        return None


def fetch_rss(
    url: str,
    source_name: str,
    max_entries: int = 3,
    fetch_fulltext: bool = False,
    fulltext_chars: int = 8000,
) -> list[RawItem]:
    """抓取 RSS feed，返回 RawItem 列表（跨天自动去重，7 天内不重复推送同一篇文章）

    fetch_fulltext: 是否用 trafilatura 抓取文章正文（默认关闭）
    fulltext_chars: 正文最大字符数，默认 8000
    """
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

        # 尝试抓取全文
        content = None
        if fetch_fulltext and link:
            content = _fetch_fulltext(link, max_chars=fulltext_chars)

        # 回退到 RSS 摘要
        if not content:
            content = summary
            if content and "<" in content:
                content = re.sub(r"<[^>]+>", " ", content)
                content = " ".join(content.split())

        if link:
            _state.mark_seen(st, "seenArticles", link)

        new_items.append(RawItem(
            source_name=source_name,
            source_type="rss",
            title=title,
            content=content or title,
            link=link,
            published=published,
        ))

    _state.save(st)
    return new_items
