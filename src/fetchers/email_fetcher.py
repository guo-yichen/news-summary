"""Email 抓取：通过 IMAP 读取 Newsletter 等邮件"""

from .base import RawItem

try:
    import imapclient
    from imapclient import IMAPClient

    IMAP_AVAILABLE = True
except ImportError:
    IMAP_AVAILABLE = False


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
