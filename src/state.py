"""全局去重状态管理

所有 fetcher 共用同一个 ~/.news-summary/state.json，
分三个命名空间：seenArticles（RSS URL）、seenTweets（推文 ID）、seenVideos（YouTube 视频 ID）
已看过的条目 7 天后自动清除。
"""

import json
import os
import time
from pathlib import Path

_STATE_FILE = Path(os.environ["NEWS_SUMMARY_STATE"]) if "NEWS_SUMMARY_STATE" in os.environ else Path.home() / ".news-summary" / "state.json"
_RETENTION_SECONDS = 7 * 86400  # 7 天


def load() -> dict:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"seenArticles": {}, "seenTweets": {}, "seenVideos": {}}


def save(state: dict) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - _RETENTION_SECONDS
    for ns in ("seenArticles", "seenTweets", "seenVideos"):
        state.setdefault(ns, {})
        state[ns] = {k: v for k, v in state[ns].items() if v > cutoff}
    _STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def is_seen(state: dict, namespace: str, key: str) -> bool:
    return key in state.get(namespace, {})


def mark_seen(state: dict, namespace: str, key: str) -> None:
    state.setdefault(namespace, {})[key] = time.time()
