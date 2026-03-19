"""将总结内容写入 Notion 数据库"""

import os
from datetime import datetime

from notion_client import Client


def _split_text(text: str, max_len: int = 2000) -> list[str]:
    """按段落拆分文本，确保每段不超过 Notion block 的字符限制"""
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_len:
            if current:
                chunks.append(current)
            # 单行超长时强制截断
            while len(line) > max_len:
                chunks.append(line[:max_len])
                line = line[max_len:]
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)
    return chunks


def _make_rich_text(text: str) -> list[dict]:
    """构建 Notion rich_text 对象，支持 **bold**，处理 2000 字符限制"""
    import re
    parts = []
    for segment in re.split(r"(\*\*[^*]+\*\*)", text[:2000]):
        if not segment:
            continue
        if segment.startswith("**") and segment.endswith("**"):
            parts.append({
                "type": "text",
                "text": {"content": segment[2:-2]},
                "annotations": {"bold": True},
            })
        else:
            # split_text handles the 2000-char limit per chunk
            for chunk in _split_text(segment, max_len=2000):
                parts.append({"type": "text", "text": {"content": chunk}})
    return parts or [{"type": "text", "text": {"content": ""}}]


def _make_heading_block(text: str, level: int = 2) -> dict:
    """构建 heading block"""
    key = f"heading_{level}"
    return {
        "object": "block",
        "type": key,
        key: {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _make_paragraph_blocks(text: str) -> list[dict]:
    """将长文本拆成多个 paragraph block，支持 bold 格式"""
    chunks = _split_text(text, max_len=2000)
    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": _make_rich_text(chunk)},
        }
        for chunk in chunks
    ]


def _make_bullet_block(text: str) -> dict:
    """构建 bulleted_list_item block"""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _make_rich_text(text[:2000])},
    }


def _make_divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def write_to_notion(
    summary_text: str,
    notion_token: str | None = None,
    database_id: str | None = None,
    date_str: str | None = None,
) -> str:
    """
    在 Notion 数据库中创建一个新页面，写入今日总结。
    返回新页面的 URL。
    """
    token = notion_token or os.environ.get("NOTION_TOKEN")
    db_id = database_id or os.environ.get("NOTION_DATABASE_ID")

    if not token:
        raise ValueError("缺少 NOTION_TOKEN 环境变量")
    if not db_id:
        raise ValueError("缺少 NOTION_DATABASE_ID 环境变量")

    client = Client(auth=token)
    today = date_str or datetime.now().strftime("%Y-%m-%d")
    title = f"📅 {today} 信息简报"

    # 将 markdown 总结按 section 拆分成 blocks
    children = _parse_summary_to_blocks(summary_text)

    # 创建页面
    page = client.pages.create(
        parent={"database_id": db_id},
        properties={
            "title": {"title": [{"text": {"content": title}}]},
        },
        children=children[:100],  # Notion API 单次最多 100 个 block
    )

    # 如果超过 100 个 block，追加剩余的
    if len(children) > 100:
        page_id = page["id"]
        for i in range(100, len(children), 100):
            client.blocks.children.append(
                block_id=page_id,
                children=children[i : i + 100],
            )

    return page["url"]


def _parse_summary_to_blocks(summary_text: str) -> list[dict]:
    """
    将 markdown 格式的总结解析成 Notion block 列表。
    简单解析：识别 ## 标题，其余作为段落。
    """
    blocks = []
    current_paragraph = []

    for line in summary_text.split("\n"):
        stripped = line.strip()

        # Markdown heading
        if stripped.startswith("## "):
            # 先把之前攒的段落输出
            if current_paragraph:
                text = "\n".join(current_paragraph)
                blocks.extend(_make_paragraph_blocks(text))
                current_paragraph = []
            blocks.append(_make_heading_block(stripped[3:], level=2))

        elif stripped.startswith("### "):
            if current_paragraph:
                text = "\n".join(current_paragraph)
                blocks.extend(_make_paragraph_blocks(text))
                current_paragraph = []
            blocks.append(_make_heading_block(stripped[4:], level=3))

        elif stripped.startswith("# "):
            if current_paragraph:
                text = "\n".join(current_paragraph)
                blocks.extend(_make_paragraph_blocks(text))
                current_paragraph = []
            blocks.append(_make_heading_block(stripped[2:], level=1))

        elif stripped.startswith("- ") or stripped.startswith("* "):
            # Flush any buffered paragraph first
            if current_paragraph:
                text = "\n".join(current_paragraph)
                blocks.extend(_make_paragraph_blocks(text))
                current_paragraph = []
            blocks.append(_make_bullet_block(stripped[2:]))

        elif stripped == "---":
            if current_paragraph:
                text = "\n".join(current_paragraph)
                blocks.extend(_make_paragraph_blocks(text))
                current_paragraph = []
            blocks.append(_make_divider())

        elif stripped == "":
            # 空行：输出当前段落
            if current_paragraph:
                text = "\n".join(current_paragraph)
                blocks.extend(_make_paragraph_blocks(text))
                current_paragraph = []
        else:
            current_paragraph.append(line)

    # 处理最后一段
    if current_paragraph:
        text = "\n".join(current_paragraph)
        blocks.extend(_make_paragraph_blocks(text))

    return blocks
