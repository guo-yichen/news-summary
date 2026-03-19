# news-summary

每天自动聚合你关注的信息源，用 AI 生成一份结构化简报，写入 Notion。

## 它每天做什么？

```
每天早上 9:00（北京时间），GitHub Actions 自动触发：

1. 抓取内容
   ├── Substack / 博客 / 播客 → 通过 RSS 拉取最新文章
   ├── YouTube → RSS 获取新视频 + 自动下载字幕全文
   ├── Twitter/X → Playwright 登录你的账号，抓取 timeline 或指定博主的推文
   └── Email Newsletter → 通过 IMAP 或 Gmail API 读取订阅邮件

2. AI 总结
   ├── 把所有抓到的内容发给 AI（Gemini 或 Claude）
   └── 生成结构化摘要：
       ├── 今日最重要的 5 条信息（跨所有来源）
       ├── 每个来源的简短摘要（2-3 句）
       └── 值得深入阅读的内容推荐（附链接）

3. 写入 Notion
   └── 在你的 Notion 数据库里创建一个新页面：
       📅 2025-03-18 信息简报
```

打开 Notion 就能看到今天的简报。想深入了解某条内容，把摘要贴回 Claude 追问即可。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium  # 只在需要 Twitter 抓取时安装
```

### 2. 配置信息源

```bash
cp sources.example.yaml sources.yaml
```

编辑 `sources.yaml`，填入你要关注的信息源。支持的类型：

| 类型 | 说明 |
|------|------|
| `rss` | Substack、博客、播客等任何 RSS 源 |
| `youtube` | YouTube 频道（自动获取视频字幕） |
| `twitter` | Twitter/X（Playwright 登录抓取） |
| `email` | 邮件订阅（IMAP） |
| `gmail` | Gmail API（需要 OAuth2 凭证） |

### 3. 设置环境变量

```bash
# AI 模型（二选一）
export AI_PROVIDER=gemini          # 或 claude
export GEMINI_API_KEY=your-key     # 用 Gemini 时设置
export ANTHROPIC_API_KEY=your-key  # 用 Claude 时设置

# Notion
export NOTION_TOKEN=your-token
export NOTION_DATABASE_ID=your-db-id

# 输出模式
export OUTPUT_MODE=notion          # notion / markdown / both
```

### 4. Twitter 登录（可选）

首次使用需要手动登录一次，保存 cookies：

```bash
python -m src.fetchers.twitter_login
```

会打开 Chrome 浏览器，手动登录 Twitter 后回到终端按 Enter。

### 5. 运行

```bash
python -m src.runner
```

## GitHub Actions 自动化

推送到 GitHub 后，在仓库 **Settings → Secrets and variables → Actions** 中添加：

| Secret | 说明 |
|--------|------|
| `SOURCES_YAML` | `sources.yaml` 的 base64 编码内容 |
| `GEMINI_API_KEY` | Gemini API Key |
| `ANTHROPIC_API_KEY` | Claude API Key（如果用 Claude） |
| `NOTION_TOKEN` | Notion Integration Token |
| `NOTION_DATABASE_ID` | Notion 数据库 ID |
| `TWITTER_COOKIES_B64` | `twitter_cookies.json` 的 base64 编码（可选） |

生成 base64：

```bash
base64 -i sources.yaml          # macOS
base64 sources.yaml              # Linux
base64 -i twitter_cookies.json   # Twitter cookies
```

Workflow 每天 UTC 01:00（北京时间 09:00）自动运行，也可以在 Actions 页面手动触发。

## Notion 设置

1. 前往 [Notion Integrations](https://www.notion.so/my-integrations) 创建一个 Integration，获取 Token
2. 创建一个 Notion 数据库（表格），确保有 `title` 属性
3. 在数据库页面点击 `...` → `Connections` → 添加你的 Integration
4. 复制数据库 ID（URL 中 `notion.so/` 后面那串 32 位字符）

## 项目结构

```
├── src/
│   ├── runner.py              # 主入口：抓取 → 总结 → 保存
│   ├── summarize.py           # AI 总结（Claude / Gemini）
│   ├── notion_writer.py       # Notion 写入
│   └── fetchers/
│       ├── base.py            # RawItem 数据结构
│       ├── rss.py             # RSS 抓取
│       ├── youtube.py         # YouTube 字幕抓取
│       ├── twitter.py         # Twitter Playwright 抓取
│       ├── twitter_login.py   # Twitter 登录辅助脚本
│       └── email_fetcher.py   # IMAP / Gmail API 邮件抓取
├── .github/workflows/
│   └── daily-summary.yml      # GitHub Actions 定时任务
├── sources.example.yaml       # 信息源配置模板
└── requirements.txt
```
