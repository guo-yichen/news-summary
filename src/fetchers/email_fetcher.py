"""Email 抓取：通过 IMAP 或 Gmail API 读取 Newsletter 等邮件"""

import base64
import os
from .base import RawItem

try:
    from imapclient import IMAPClient

    IMAP_AVAILABLE = True
except ImportError:
    IMAP_AVAILABLE = False

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False


def fetch_email(
    imap_server: str,
    email: str,
    password: str,
    source_name: str,
    folder: str = "INBOX",
    search_from: str | None = None,
    max_emails: int = 5,
) -> list[RawItem]:
    """通过 IMAP 抓取邮件"""
    if not IMAP_AVAILABLE:
        return [
            RawItem(
                source_name=source_name,
                source_type="email",
                title="[未安装 imapclient]",
                content="请运行: pip install imapclient",
                link=None,
            )
        ]

    items: list[RawItem] = []
    try:
        with IMAPClient(imap_server, use_uid=True) as client:
            client.login(email, password)
            client.select_folder(folder)

            if search_from:
                messages = client.search(["FROM", search_from])
            else:
                messages = client.search(["UNSEEN"])  # 或 ALL

            if not messages:
                return items

            # 取最新的 N 条
            for uid in reversed(messages[-max_emails:]):
                try:
                    msg = client.fetch([uid], ["ENVELOPE", "BODY[TEXT]"])
                    env = msg[uid].get(b"ENVELOPE")
                    body = msg[uid].get(b"BODY[TEXT]", b"")

                    if env is None:
                        continue

                    subject = env.subject
                    if subject:
                        title = subject.decode("utf-8", errors="replace") if isinstance(subject, bytes) else str(subject)
                    else:
                        title = "(无主题)"

                    content = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
                    # 截断过长的邮件
                    if len(content) > 3000:
                        content = content[:3000] + "\n...[截断]"

                    date = env.date
                    published = date.strftime("%Y-%m-%d %H:%M") if date else None

                    items.append(
                        RawItem(
                            source_name=source_name,
                            source_type="email",
                            title=title,
                            content=content,
                            link=None,
                            published=published,
                        )
                    )
                except Exception as e:
                    items.append(
                        RawItem(
                            source_name=source_name,
                            source_type="email",
                            title="[解析失败]",
                            content=str(e),
                            link=None,
                        )
                    )

    except Exception as e:
        items.append(
            RawItem(
                source_name=source_name,
                source_type="email",
                title="[连接失败]",
                content=str(e),
                link=None,
            )
        )

    return items


def fetch_gmail(
    source_name: str,
    credentials_json: str | None = None,
    query: str = "is:unread",
    max_emails: int = 5,
) -> list[RawItem]:
    """
    通过 Gmail API 抓取邮件。

    credentials_json: OAuth2 credentials JSON 文件路径，默认读 GMAIL_CREDENTIALS 环境变量
    query: Gmail 搜索语法，如 "from:newsletter@example.com" 或 "is:unread"
    """
    if not GMAIL_API_AVAILABLE:
        return [
            RawItem(
                source_name=source_name,
                source_type="email",
                title="[依赖缺失]",
                content="需要安装: pip install google-api-python-client google-auth",
                link=None,
            )
        ]

    creds_path = credentials_json or os.environ.get("GMAIL_CREDENTIALS", "gmail_credentials.json")

    try:
        creds = Credentials.from_authorized_user_file(creds_path, ["https://www.googleapis.com/auth/gmail.readonly"])
        service = build("gmail", "v1", credentials=creds)

        results = service.users().messages().list(userId="me", q=query, maxResults=max_emails).execute()
        messages = results.get("messages", [])

        items: list[RawItem] = []
        for msg_info in messages:
            msg = service.users().messages().get(userId="me", id=msg_info["id"], format="full").execute()

            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            subject = headers.get("Subject", "(无主题)")
            date = headers.get("Date", "")

            body = _extract_gmail_body(msg["payload"])
            if len(body) > 3000:
                body = body[:3000] + "\n...[截断]"

            items.append(
                RawItem(
                    source_name=source_name,
                    source_type="email",
                    title=subject,
                    content=body,
                    link=None,
                    published=date,
                )
            )

        return items

    except Exception as e:
        return [
            RawItem(
                source_name=source_name,
                source_type="email",
                title="[Gmail API 失败]",
                content=str(e),
                link=None,
            )
        ]


def _extract_gmail_body(payload: dict) -> str:
    """从 Gmail API payload 中提取纯文本正文"""
    if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _extract_gmail_body(part)
        if result:
            return result

    if payload.get("mimeType") == "text/html" and "data" in payload.get("body", {}):
        import re
        html = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        text = re.sub(r"<[^>]+>", " ", html)
        return " ".join(text.split())

    return ""
