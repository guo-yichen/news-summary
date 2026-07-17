"""Render daily summaries as standalone HTML files."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path


def _convert_inline_markdown(text: str) -> str:
    """Convert the small markdown subset used by summaries into HTML."""
    escaped = html.escape(text)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        escaped,
    )
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def _summary_markdown_to_html(summary_text: str) -> str:
    """Convert summary markdown into readable HTML without extra dependencies."""
    lines = summary_text.splitlines()
    html_lines: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            html_lines.append(f"<p>{_convert_inline_markdown(text)}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            close_list()
            continue

        if stripped == "---":
            flush_paragraph()
            close_list()
            html_lines.append("<hr>")
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            close_list()
            level = len(heading_match.group(1))
            text = _convert_inline_markdown(heading_match.group(2))
            html_lines.append(f"<h{level}>{text}</h{level}>")
            continue

        list_match = re.match(r"^[-*]\s+(.+)$", stripped)
        if list_match:
            flush_paragraph()
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_convert_inline_markdown(list_match.group(1))}</li>")
            continue

        paragraph.append(line)

    flush_paragraph()
    close_list()
    return "\n".join(html_lines)


def _document(title: str, date: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17201b;
      --muted: #647169;
      --line: #d9e1dc;
      --paper: #f7f5ee;
      --panel: #fffdf7;
      --mint: #d9efe3;
      --sage: #6f9b84;
      --coral: #e8876f;
      --blue: #6f94b8;
      --shadow: 0 18px 55px rgba(37, 49, 43, 0.12);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        linear-gradient(135deg, rgba(217, 239, 227, 0.82), rgba(247, 245, 238, 0.08) 34%),
        linear-gradient(225deg, rgba(232, 135, 111, 0.16), rgba(247, 245, 238, 0) 40%),
        var(--paper);
      color: var(--ink);
      line-height: 1.58;
    }}

    a {{
      color: #315f8b;
      text-decoration: none;
      font-weight: 650;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    .shell {{
      width: min(960px, calc(100% - 32px));
      margin: 0 auto;
      padding: 42px 0 64px;
    }}

    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
      padding: 32px 0 28px;
      border-bottom: 1px solid rgba(23, 32, 27, 0.16);
    }}

    .kicker {{
      margin: 0 0 10px;
      color: var(--sage);
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }}

    h1 {{
      max-width: 760px;
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(40px, 7vw, 76px);
      line-height: 0.96;
      letter-spacing: 0;
    }}

    .date-chip {{
      display: inline-flex;
      align-items: center;
      min-height: 42px;
      padding: 10px 14px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 253, 247, 0.74);
      color: var(--muted);
      font-size: 14px;
      white-space: nowrap;
    }}

    .summary {{
      margin-top: 28px;
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 253, 247, 0.86);
      box-shadow: var(--shadow);
    }}

    .summary h1 {{
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
      font-size: 30px;
      line-height: 1.16;
      margin: 0 0 18px;
    }}

    .summary h2 {{
      margin: 34px 0 14px;
      padding-top: 18px;
      border-top: 1px solid rgba(23, 32, 27, 0.12);
      font-size: 23px;
      letter-spacing: 0;
    }}

    .summary h3 {{
      margin: 24px 0 10px;
      font-size: 18px;
      letter-spacing: 0;
    }}

    .summary p {{
      margin: 0 0 14px;
      color: var(--muted);
      font-size: 16px;
    }}

    .summary ul {{
      margin: 0 0 18px;
      padding-left: 22px;
    }}

    .summary li {{
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 16px;
    }}

    .summary strong {{
      color: var(--ink);
    }}

    hr {{
      height: 1px;
      margin: 30px 0;
      border: 0;
      background: rgba(23, 32, 27, 0.14);
    }}

    footer {{
      margin-top: 24px;
      color: var(--muted);
      font-size: 13px;
    }}

    @media (max-width: 760px) {{
      header {{
        grid-template-columns: 1fr;
        align-items: start;
      }}

      .summary {{
        padding: 20px;
      }}

      .date-chip {{
        width: fit-content;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <p class="kicker">Daily AI Digest</p>
        <h1>{html.escape(title)}</h1>
      </div>
      <div class="date-chip">{html.escape(date)}</div>
    </header>
    <article class="summary">
      {body_html}
    </article>
    <footer>Generated by news-summary.</footer>
  </main>
</body>
</html>
"""


def write_html_summary(
    summary_text: str,
    date: str,
    output_dir: str = "briefs",
    language: str = "zh",
) -> Path:
    """Write dated and latest HTML summary files. Returns dated file path."""
    title_map = {
        "zh": f"每日 AI 摘要 {date}",
        "en": f"Daily AI Summary {date}",
        "bilingual": f"每日 AI 摘要 / Daily AI Summary {date}",
    }
    title = title_map.get(language, f"Daily AI Summary {date}")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    body_html = _summary_markdown_to_html(summary_text)
    doc = _document(title=title, date=date, body_html=body_html)

    dated_path = output_path / f"{date}.html"
    latest_path = output_path / "latest.html"
    dated_path.write_text(doc, encoding="utf-8")
    shutil.copyfile(dated_path, latest_path)
    return dated_path
