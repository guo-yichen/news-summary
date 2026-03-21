"""通过 Gmail SMTP 发送每日摘要邮件"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(
    summary_text: str,
    date: str,
    smtp_user: str,
    smtp_password: str,
    to_address: str,
    language: str = "zh",
) -> None:
    title_map = {
        "zh": f"每日 AI 摘要 {date}",
        "en": f"Daily AI Summary {date}",
        "bilingual": f"每日 AI 摘要 / Daily AI Summary {date}",
    }
    subject = title_map.get(language, f"每日 AI 摘要 {date}")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_address

    # 纯文本版本
    msg.attach(MIMEText(summary_text, "plain", "utf-8"))

    # HTML 版本：把 markdown 粗体/标题简单转换，方便手机阅读
    html_body = summary_text
    import re
    html_body = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html_body)
    # markdown 链接 [text](url) → <a href>
    html_body = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" style="color:#1a73e8">\1</a>', html_body)
    html_body = html_body.replace("\n", "<br>\n")
    html_body = f"<html><body style='font-family:sans-serif;max-width:800px;margin:auto;padding:20px'>{html_body}</body></html>"
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_address, msg.as_bytes())
