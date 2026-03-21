# News Summary — AI 每日信息简报

**[English](#english) | [中文](#chinese)**

---

<a name="english"></a>
# 📰 News Summary — Daily AI Digest

An automated pipeline that aggregates your personal information sources every day, uses Claude AI to generate a structured digest, and delivers it to your inbox and Notion — all running on GitHub Actions for free.

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| **30+ source types** | RSS, Substack, blogs, podcasts, YouTube transcripts, Twitter/X timeline, newsletters | ✅ |
| **Smart deduplication** | Tracks seen articles across days — no repeats | ✅ |
| **Age filtering** | Skips articles older than 30 days by default | ✅ |
| **Claude AI summaries** | Structured digest with highlights, bullet points, and source-by-source breakdown | ✅ |
| **Multilingual output** | Chinese (`zh`), English (`en`), or bilingual (`bilingual`) | ✅ |
| **Notion integration** | Creates a new page daily with clickable links | ✅ |
| **Email delivery** | Sends HTML email with clickable links to multiple recipients | ✅ |
| **GitHub Actions** | Runs automatically every day at 9:00 AM Beijing time — no server needed | ✅ |
| **No updates? Still shows** | Sources with no new content are listed as "no updates today" so you know they were checked | ✅ |
| **Telegram notifications** | Push digest to Telegram on completion | 🚧 untested |

## 🗂️ Supported Source Types

| Type | Examples |
|------|---------|
| `rss` | Substack, personal blogs, news sites, podcasts |
| `youtube_transcript` | YouTube channels — fetches full transcripts via Supadata API |
| `follow_builders_x` | Curated AI builders Twitter feed (no API key needed) |
| `follow_builders_podcasts` | Top AI podcasts with transcripts (no API key needed) |
| `twitter` | Your personal Twitter/X timeline via Playwright + cookies |
| `email` | Email newsletters via IMAP |
| `gmail` | Gmail via OAuth2 API |

## 🚀 Quick Start

### 1. Clone and install

```bash
git clone https://github.com/guo-yichen/news-summary.git
cd news-summary
pip install -r requirements.txt
```

### 2. Configure sources

```bash
cp sources.example.yaml sources.yaml
```

Edit `sources.yaml` with your sources. See `sources.example.yaml` for all options.

Set the output language at the top:
```yaml
language: zh        # zh | en | bilingual
```

### 3. Set environment variables

```bash
export ANTHROPIC_API_KEY=your-claude-api-key

# Notion (optional)
export NOTION_TOKEN=your-notion-token
export NOTION_DATABASE_ID=your-database-id

# Email (optional)
export EMAIL_USER=you@gmail.com
export EMAIL_PASSWORD=your-app-password   # Gmail app-specific password
export EMAIL_TO=you@gmail.com,other@example.com

# Telegram (optional)
export TELEGRAM_BOT_TOKEN=your-bot-token
export TELEGRAM_CHAT_ID=your-chat-id

# Output mode
export OUTPUT_MODE=both    # notion | markdown | both
```

### 4. Run

```bash
python -m src.runner
```

Depending on your configuration, the digest will be:
- Saved to `summaries/YYYY-MM-DD.md` (when `OUTPUT_MODE=markdown` or `both`)
- Written to Notion as a new page (when `OUTPUT_MODE=notion` or `both`)
- Sent to your inbox as an HTML email with clickable links (when `EMAIL_USER` + `EMAIL_PASSWORD` are set)

### 5. Twitter/X timeline (optional)

To include your personal Twitter timeline:

1. Install [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) browser extension
2. Log in to x.com
3. Click Cookie-Editor → Export → Export as JSON (copies to clipboard)
4. Run `pbpaste > twitter_cookies.json` in your terminal

Then add to `sources.yaml`:
```yaml
- type: twitter
  name: "My Twitter Timeline"
  max_tweets: 30
```

## ⚙️ GitHub Actions Setup

Fork this repo, then go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `SOURCES_YAML` | Base64-encoded content of your `sources.yaml` |
| `ANTHROPIC_API_KEY` | Claude API key |
| `NOTION_TOKEN` | Notion integration token |
| `NOTION_DATABASE_ID` | Notion database ID |
| `EMAIL_USER` | Gmail address for sending |
| `EMAIL_PASSWORD` | Gmail app-specific password |
| `EMAIL_TO` | Recipient email(s), comma-separated |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID (optional) |
| `SUPADATA_API_KEY` | Supadata API key for YouTube transcripts (optional) |
| `TWITTER_COOKIES` | Base64-encoded `twitter_cookies.json` (optional) |

Generate base64 for `sources.yaml`:
```bash
base64 -i sources.yaml | tr -d '\n' | gh secret set SOURCES_YAML
```

The workflow runs daily at **01:00 UTC (09:00 Beijing)**. You can also trigger it manually from the Actions tab.

## 🔧 Notion Setup

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → New Integration → copy the token
2. Create a Notion database with a `title` property
3. Open the database → `...` → Connections → add your integration
4. Copy the database ID from the URL (the 32-character string after `notion.so/`)

## 📁 Project Structure

```
├── src/
│   ├── runner.py                  # Main entry: fetch → summarize → save
│   ├── summarize.py               # Claude AI summarization
│   ├── notion_writer.py           # Notion page writer
│   ├── email_sender.py            # Gmail SMTP sender
│   ├── telegram_notifier.py       # Telegram push
│   ├── state.py                   # Cross-day deduplication state
│   └── fetchers/
│       ├── base.py                # RawItem data structure
│       ├── rss.py                 # RSS fetcher
│       ├── follow_builders.py     # follow-builders Twitter + podcast feeds
│       ├── youtube_transcript.py  # YouTube transcript via Supadata
│       ├── twitter.py             # Twitter timeline via Playwright
│       ├── twitter_login.py       # Twitter login helper
│       └── email_fetcher.py       # IMAP / Gmail fetcher
├── .github/workflows/
│   └── daily-summary.yml          # GitHub Actions workflow
├── sources.example.yaml           # Source configuration template
└── requirements.txt
```

## 🙏 Credits

- [follow-builders](https://github.com/zarazhangrui/follow-builders) by [Zara Zhang](https://github.com/zarazhangrui) — the `follow_builders_x` and `follow_builders_podcasts` source types are inspired by and built on top of her centralized AI builders feed. No API key required thanks to her work.

---

<a name="chinese"></a>
# 📰 News Summary — AI 每日信息简报

每天自动聚合你关注的信息源，用 Claude AI 生成结构化简报，发送到你的邮箱和 Notion — 完全运行在 GitHub Actions 上，免费，无需服务器。

## ✨ 功能特性

| 功能 | 说明 | 状态 |
|------|------|------|
| **30+ 种信息源** | RSS、Substack、博客、播客、YouTube 字幕、Twitter/X 时间线、Newsletter | ✅ |
| **跨日去重** | 追踪已读文章，不重复推送 | ✅ |
| **时效过滤** | 默认跳过 30 天前的旧文章 | ✅ |
| **Claude AI 总结** | 结构化简报：今日要点 + bullet points + 来源详情 | ✅ |
| **多语言输出** | 中文（`zh`）、英文（`en`）、中英双语（`bilingual`）| ✅ |
| **Notion 集成** | 每天在 Notion 数据库创建新页面，链接可点击 | ✅ |
| **邮件推送** | 发送 HTML 格式邮件，链接可点击，支持多个收件人 | ✅ |
| **GitHub Actions** | 每天北京时间 9:00 自动运行，无需服务器 | ✅ |
| **无更新也显示** | 没有新内容的来源会标注「今日无新内容」，让你确认它被检查过 | ✅ |
| **Telegram 通知** | 生成完成后推送到 Telegram | 🚧 未测试 |

## 🗂️ 支持的信息源类型

| 类型 | 示例 |
|------|------|
| `rss` | Substack、博客、新闻网站、播客 |
| `youtube_transcript` | YouTube 频道（通过 Supadata API 获取完整字幕）|
| `follow_builders_x` | AI 大佬 Twitter 精选 Feed（无需 API key）|
| `follow_builders_podcasts` | 顶级 AI 播客字幕（无需 API key）|
| `twitter` | 你的个人 Twitter/X 时间线（Playwright + cookies）|
| `email` | 邮件 Newsletter（IMAP）|
| `gmail` | Gmail（OAuth2 API）|

## 🚀 快速开始

### 1. 克隆并安装依赖

```bash
git clone https://github.com/guo-yichen/news-summary.git
cd news-summary
pip install -r requirements.txt
```

### 2. 配置信息源

```bash
cp sources.example.yaml sources.yaml
```

编辑 `sources.yaml`，填入你要关注的信息源。参考 `sources.example.yaml` 查看所有配置选项。

在文件顶部设置输出语言：
```yaml
language: zh        # zh | en | bilingual
```

### 3. 设置环境变量

```bash
export ANTHROPIC_API_KEY=你的-claude-api-key

# Notion（可选）
export NOTION_TOKEN=你的-notion-token
export NOTION_DATABASE_ID=你的-数据库-id

# 邮件（可选）
export EMAIL_USER=you@gmail.com
export EMAIL_PASSWORD=你的-应用专用密码   # Gmail 应用专用密码
export EMAIL_TO=you@gmail.com,other@example.com

# Telegram（可选）
export TELEGRAM_BOT_TOKEN=你的-bot-token
export TELEGRAM_CHAT_ID=你的-chat-id

# 输出模式
export OUTPUT_MODE=both    # notion | markdown | both
```

### 4. 运行

```bash
python -m src.runner
```

根据你的配置，生成的简报会：
- 保存为 `summaries/YYYY-MM-DD.md`（`OUTPUT_MODE=markdown` 或 `both` 时）
- 写入 Notion 数据库（`OUTPUT_MODE=notion` 或 `both` 时）
- 以 HTML 格式发送到邮箱，链接可点击（配置了 `EMAIL_USER` + `EMAIL_PASSWORD` 时）

### 5. Twitter/X 时间线（可选）

如需抓取你的个人 Twitter 时间线：

1. 安装浏览器扩展 [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
2. 登录 x.com
3. 点击 Cookie-Editor → Export → Export as JSON（自动复制到剪贴板）
4. 在终端运行 `pbpaste > twitter_cookies.json`

然后在 `sources.yaml` 里添加：
```yaml
- type: twitter
  name: "我的 Twitter 时间线"
  max_tweets: 30
```

## ⚙️ GitHub Actions 自动化

Fork 本仓库，然后在 **Settings → Secrets and variables → Actions** 中添加以下 Secrets：

| Secret | 说明 |
|--------|------|
| `SOURCES_YAML` | `sources.yaml` 的 base64 编码内容 |
| `ANTHROPIC_API_KEY` | Claude API Key |
| `NOTION_TOKEN` | Notion Integration Token |
| `NOTION_DATABASE_ID` | Notion 数据库 ID |
| `EMAIL_USER` | 发件 Gmail 地址 |
| `EMAIL_PASSWORD` | Gmail 应用专用密码 |
| `EMAIL_TO` | 收件地址，多个用逗号分隔 |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token（可选）|
| `TELEGRAM_CHAT_ID` | Telegram chat ID（可选）|
| `SUPADATA_API_KEY` | Supadata API Key，用于 YouTube 字幕（可选）|
| `TWITTER_COOKIES` | `twitter_cookies.json` 的 base64 编码（可选）|

生成 `sources.yaml` 的 base64：
```bash
base64 -i sources.yaml | tr -d '\n' | gh secret set SOURCES_YAML
```

Workflow 每天 **UTC 01:00（北京时间 09:00）** 自动运行，也可在 Actions 页面手动触发。

## 🔧 Notion 配置

1. 前往 [notion.so/my-integrations](https://www.notion.so/my-integrations) → 新建 Integration → 复制 token
2. 创建一个 Notion 数据库，确保有 `title` 属性
3. 打开数据库 → `...` → Connections → 添加你的 Integration
4. 从 URL 中复制数据库 ID（`notion.so/` 后面的 32 位字符串）

## 📁 项目结构

```
├── src/
│   ├── runner.py                  # 主入口：抓取 → 总结 → 保存
│   ├── summarize.py               # Claude AI 总结
│   ├── notion_writer.py           # Notion 页面写入
│   ├── email_sender.py            # Gmail SMTP 发送
│   ├── telegram_notifier.py       # Telegram 推送
│   ├── state.py                   # 跨日去重状态管理
│   └── fetchers/
│       ├── base.py                # RawItem 数据结构
│       ├── rss.py                 # RSS 抓取
│       ├── follow_builders.py     # follow-builders Twitter + 播客 Feed
│       ├── youtube_transcript.py  # YouTube 字幕（Supadata）
│       ├── twitter.py             # Twitter 时间线（Playwright）
│       ├── twitter_login.py       # Twitter 登录辅助
│       └── email_fetcher.py       # IMAP / Gmail 抓取
├── .github/workflows/
│   └── daily-summary.yml          # GitHub Actions 定时任务
├── sources.example.yaml           # 信息源配置模板
└── requirements.txt
```

## 🙏 致谢

- [follow-builders](https://github.com/zarazhangrui/follow-builders) by [Zara Zhang](https://github.com/zarazhangrui) — `follow_builders_x` 和 `follow_builders_podcasts` 两种信息源类型借鉴自她维护的 AI 大佬中央 Feed，无需任何 API key 即可使用。
