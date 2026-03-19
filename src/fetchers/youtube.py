"""YouTube 抓取：通过 RSS 获取最新视频，用 youtube-transcript-api 获取字幕"""

import re
import feedparser
from .base import RawItem


def _extract_video_id(url: str) -> str | None:
    """从 YouTube URL 中提取 video ID"""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _get_transcript(video_id: str, languages: list[str] | None = None) -> str | None:
    """获取 YouTube 视频字幕文本"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt_api = YouTubeTranscriptApi()
        langs = languages or ["zh-Hans", "zh", "en"]
        transcript = ytt_api.fetch(video_id, languages=langs)
        # 拼接字幕文本，截断到合理长度
        text = " ".join(snippet.text for snippet in transcript.snippets)
        if len(text) > 5000:
            text = text[:5000] + "..."
        return text
    except Exception:
        return None


def fetch_youtube(
    rss_url: str,
    source_name: str,
    max_entries: int = 3,
    languages: list[str] | None = None,
) -> list[RawItem]:
    """
    抓取 YouTube 频道 RSS，对每个视频尝试获取字幕。
    rss_url 格式: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
    """
    items: list[RawItem] = []

    try:
        feed = feedparser.parse(rss_url, request_headers={"User-Agent": "NewsSummary/1.0"})
    except Exception as e:
        return [RawItem(source_name=source_name, source_type="youtube", title="[抓取失败]", content=str(e), link=rss_url)]

    for entry in feed.entries[:max_entries]:
        title = entry.get("title", "(无标题)")
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", ""))

        # 尝试获取字幕
        video_id = _extract_video_id(link)
        transcript = None
        if video_id:
            transcript = _get_transcript(video_id, languages)

        if transcript:
            content = f"[字幕内容]\n{transcript}"
        else:
            # fallback 到 RSS 摘要
            summary = entry.get("summary", entry.get("description", ""))
            if summary and "<" in summary:
                summary = re.sub(r"<[^>]+>", " ", summary)
                summary = " ".join(summary.split())
            content = summary or title

        items.append(
            RawItem(
                source_name=source_name,
                source_type="youtube",
                title=title,
                content=content,
                link=link,
                published=published,
            )
        )

    return items
