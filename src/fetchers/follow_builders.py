"""从 follow-builders 中央 Feed 抓取 Twitter 和播客内容（无需 API key）

数据源: https://github.com/zarazhangrui/follow-builders
  - feed-x.json:       AI 大佬的 Twitter 推文（24h 内）
  - feed-podcasts.json: AI 播客最新一集的字幕（72h 内）
"""

import json
import urllib.request
from .base import RawItem
from src import state as _state

_BASE = "https://raw.githubusercontent.com/zarazhangrui/follow-builders/main"
_FEED_X = f"{_BASE}/feed-x.json"
_FEED_PODCASTS = f"{_BASE}/feed-podcasts.json"


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "NewsSummary/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_follow_builders_x(max_tweets_per_person: int = 3) -> list[RawItem]:
    """抓取 follow-builders 的 Twitter feed，每人最多取 max_tweets_per_person 条（推文 ID 去重）"""
    try:
        data = _fetch_json(_FEED_X)
    except Exception as e:
        return [RawItem(source_name="follow-builders/X", source_type="follow_builders",
                        title="[抓取失败]", content=str(e), link=_FEED_X)]

    st = _state.load()
    items: list[RawItem] = []
    for person in data.get("x", []):
        name = person.get("name", person.get("handle", "未知"))
        handle = person.get("handle", "")
        count = 0
        for tweet in person.get("tweets", []):
            if count >= max_tweets_per_person:
                break
            tweet_id = tweet.get("id", tweet.get("url", ""))
            if tweet_id and _state.is_seen(st, "seenTweets", tweet_id):
                continue
            if tweet_id:
                _state.mark_seen(st, "seenTweets", tweet_id)
            items.append(RawItem(
                source_name=f"@{handle} ({name})",
                source_type="follow_builders",
                title=tweet.get("text", "")[:80],
                content=tweet.get("text", ""),
                link=tweet.get("url"),
                published=tweet.get("createdAt"),
            ))
            count += 1
    _state.save(st)
    return items


def fetch_follow_builders_podcasts(max_episodes: int = 3, transcript_chars: int = 2000) -> list[RawItem]:
    """抓取 follow-builders 的播客 feed，字幕截取前 transcript_chars 个字符（视频 ID 去重）"""
    try:
        data = _fetch_json(_FEED_PODCASTS)
    except Exception as e:
        return [RawItem(source_name="follow-builders/Podcasts", source_type="follow_builders",
                        title="[抓取失败]", content=str(e), link=_FEED_PODCASTS)]

    st = _state.load()
    items: list[RawItem] = []
    for ep in data.get("podcasts", []):
        if len(items) >= max_episodes:
            break
        video_id = ep.get("videoId", ep.get("url", ""))
        if video_id and _state.is_seen(st, "seenVideos", video_id):
            continue
        if video_id:
            _state.mark_seen(st, "seenVideos", video_id)
        transcript = ep.get("transcript", "")
        if len(transcript) > transcript_chars:
            transcript = transcript[:transcript_chars] + "…（字幕已截断）"
        items.append(RawItem(
            source_name=ep.get("name", "未知播客"),
            source_type="follow_builders",
            title=ep.get("title", "(无标题)"),
            content=transcript or ep.get("title", ""),
            link=ep.get("url"),
            published=ep.get("publishedAt"),
        ))
    _state.save(st)
    return items
