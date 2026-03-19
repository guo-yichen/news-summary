"""使用 Claude 对抓取的内容进行总结"""

import anthropic
from src.fetchers.base import RawItem

SYSTEM_PROMPT = """你是一个信息助手。将下面的内容总结成结构化的 Markdown：

1. **今日最重要的 5 条信息**（跨所有来源，按重要性排序）
2. **每个来源的简短摘要**（2-3 句）
3. **值得深入阅读的内容推荐**（附链接或标题）

输出使用 Markdown 格式，清晰易读。如果某条内容特别重要，可以加粗或标注。"""


def build_user_content(items: list[RawItem]) -> str:
    """将 RawItem 列表拼接成送给 Claude 的文本"""
    parts = []
    for item in items:
        part = f"[{item.source_name}] {item.title}\n{item.content}"
        if item.link:
            part += f"\n链接: {item.link}"
        parts.append(part)
    return "\n\n---\n\n".join(parts)


def summarize(items: list[RawItem], api_key: str | None = None, model: str = "claude-sonnet-4-20250514") -> str:
    """调用 Claude 生成总结"""
    if not items:
        return "# 今日摘要\n\n暂无新内容。"

    content = build_user_content(items)

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text
