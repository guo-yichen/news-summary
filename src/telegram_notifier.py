"""通过 Telegram Bot 推送每日摘要

配置方式（sources.yaml 顶层）：
  telegram:
    bot_token: "123456:ABC..."   # @BotFather 创建的 token
    chat_id: "123456789"         # 个人或群组的 chat ID

获取步骤：
1. 在 Telegram 搜索 @BotFather，发送 /newbot，按提示创建 bot，获得 token
2. 向你的 bot 发一条任意消息
3. 浏览器访问 https://api.telegram.org/bot<TOKEN>/getUpdates
4. 在返回 JSON 的 result[0].message.chat.id 找到你的 chat_id
"""

import json
import re
import urllib.request
from datetime import datetime

_MAX_LEN = 4000  # Telegram 单消息上限 4096，留余量


def _md_to_html(text: str) -> str:
    """将 Markdown 转成 Telegram HTML（支持加粗、标题、链接、bullet）"""
    # 先转义 HTML 特殊字符
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # ## / ### 标题 → <b>标题</b>
    text = re.sub(r"^#{1,3}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    # **bold** → <b>bold</b>
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    # [text](url) → <a href="url">text</a>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # - / * bullet → •
    text = re.sub(r"^[-*]\s+", "• ", text, flags=re.MULTILINE)
    return text


def _split_message(text: str, max_len: int = _MAX_LEN) -> list[str]:
    """按段落切分长文本，每段不超过 max_len 字符"""
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        chunk = paragraph + "\n\n"
        if len(current) + len(chunk) > max_len:
            if current:
                chunks.append(current.rstrip())
            # 单段本身超长时强制截断
            while len(chunk) > max_len:
                chunks.append(chunk[:max_len])
                chunk = chunk[max_len:]
            current = chunk
        else:
            current += chunk
    if current.strip():
        chunks.append(current.rstrip())
    return chunks


def _send_message(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    body = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result.get('description', result)}")


def send_to_telegram(
    summary_text: str,
    bot_token: str,
    chat_id: str,
    date: str | None = None,
) -> int:
    """将摘要转换成 HTML 后分段发送到 Telegram，返回发送的消息数"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    html = _md_to_html(f"<b>每日摘要 {date}</b>\n\n" + summary_text)
    chunks = _split_message(html)
    for chunk in chunks:
        _send_message(bot_token, chat_id, chunk)
    return len(chunks)
