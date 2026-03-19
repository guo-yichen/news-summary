"""通过 Supadata API 抓取 YouTube 频道/播放列表的最新一集字幕

逻辑直接移植自 follow-builders/scripts/generate-feed.js 的 fetchYouTubeContent()
需要环境变量: SUPADATA_API_KEY
注册免费 key: https://dash.supadata.ai（免费 100 credits/月）

sources.yaml 配置示例：
  - type: youtube_transcript
    name: "Latent Space Podcast"
    channel_handle: "@latentspacepod"   # 二选一
    # playlist_id: "PLxxxxxx"           # 或用播放列表 ID
    lookback_hours: 72                  # 可选，默认 72
"""

import json
import os
import time
import urllib.parse
import urllib.request
from .base import RawItem
from src import state as _state

_SUPADATA_BASE = "https://api.supadata.ai/v1"


def _get(url: str, api_key: str) -> dict:
    req = urllib.request.Request(url, headers={"x-api-key": api_key, "User-Agent": "NewsSummary/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_youtube_transcript(
    source_name: str,
    channel_handle: str | None = None,
    playlist_id: str | None = None,
    lookback_hours: int = 72,
    api_key: str | None = None,
) -> list[RawItem]:
    """抓取频道/播放列表最新未看过的一集字幕，返回 RawItem 列表"""

    api_key = api_key or os.environ.get("SUPADATA_API_KEY")
    if not api_key:
        return [RawItem(source_name=source_name, source_type="youtube_transcript",
                        title="[配置错误]", content="缺少 SUPADATA_API_KEY 环境变量", link=None)]

    if not channel_handle and not playlist_id:
        return [RawItem(source_name=source_name, source_type="youtube_transcript",
                        title="[配置错误]", content="需要 channel_handle 或 playlist_id", link=None)]

    st = _state.load()
    cutoff_ts = time.time() - lookback_hours * 3600
    errors: list[str] = []

    # 1. 拿视频 ID 列表
    try:
        if playlist_id:
            videos_url = f"{_SUPADATA_BASE}/youtube/playlist/videos?id={urllib.parse.quote(playlist_id)}"
        else:
            videos_url = f"{_SUPADATA_BASE}/youtube/channel/videos?id={urllib.parse.quote(channel_handle)}&type=video"
        videos_data = _get(videos_url, api_key)
        video_ids = videos_data.get("videoIds") or videos_data.get("video_ids") or []
    except Exception as e:
        return [RawItem(source_name=source_name, source_type="youtube_transcript",
                        title="[抓取失败]", content=f"获取视频列表失败: {e}", link=None)]

    # 2. 取前 2 个视频的 metadata，过滤出窗口内且未看过的
    candidates = []
    for video_id in video_ids[:2]:
        if _state.is_seen(st, "seenVideos", video_id):
            continue
        try:
            meta = _get(f"{_SUPADATA_BASE}/youtube/video?id={urllib.parse.quote(video_id)}", api_key)
            published_str = meta.get("uploadDate") or meta.get("publishedAt") or meta.get("date")
            if not published_str:
                continue
            # 解析时间（ISO 8601）
            from datetime import datetime, timezone
            try:
                published_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                published_ts = published_dt.timestamp()
            except Exception:
                continue
            candidates.append({
                "video_id": video_id,
                "title": meta.get("title", "Untitled"),
                "published_ts": published_ts,
                "published_str": published_str,
            })
            time.sleep(0.3)
        except Exception as e:
            errors.append(f"获取 {video_id} metadata 失败: {e}")

    # 3. 过滤时间窗口，取最老的一集（同 follow-builders 的逻辑）
    within_window = [c for c in candidates if c["published_ts"] >= cutoff_ts]
    within_window.sort(key=lambda c: c["published_ts"])

    if not within_window:
        msg = f"最近 {lookback_hours}h 内无新集数" + (f"；错误: {'; '.join(errors)}" if errors else "")
        return [RawItem(source_name=source_name, source_type="youtube_transcript",
                        title="[暂无新内容]", content=msg, link=None)]

    selected = within_window[0]

    # 4. 拿字幕
    try:
        video_url = f"https://www.youtube.com/watch?v={selected['video_id']}"
        transcript_data = _get(
            f"{_SUPADATA_BASE}/youtube/transcript?url={urllib.parse.quote(video_url)}&text=true",
            api_key,
        )
        transcript = transcript_data.get("content", "")
    except Exception as e:
        return [RawItem(source_name=source_name, source_type="youtube_transcript",
                        title=selected["title"],
                        content=f"字幕获取失败: {e}",
                        link=f"https://youtube.com/watch?v={selected['video_id']}",
                        published=selected["published_str"])]

    # 5. 记录已看，保存 state
    _state.mark_seen(st, "seenVideos", selected["video_id"])
    _state.save(st)

    return [RawItem(
        source_name=source_name,
        source_type="youtube_transcript",
        title=selected["title"],
        content=transcript,
        link=f"https://youtube.com/watch?v={selected['video_id']}",
        published=selected["published_str"],
    )]
