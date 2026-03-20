"""Twitter/X 抓取：使用 Playwright 加载 cookies 登录，抓取 timeline 或指定用户推文"""

import json
from pathlib import Path

from .base import RawItem


def fetch_twitter(
    cookies_path: str = "twitter_cookies.json",
    source_name: str = "Twitter",
    usernames: list[str] | None = None,
    max_tweets: int = 20,
) -> list[RawItem]:
    """
    使用 Playwright 抓取 Twitter 推文。

    如果 usernames 为空，抓取 timeline（首页）。
    如果指定了 usernames，抓取每个用户的最新推文。
    """
    cookies_file = Path(cookies_path)
    if not cookies_file.exists():
        return [
            RawItem(
                source_name=source_name,
                source_type="twitter",
                title="[配置错误]",
                content=f"找不到 cookies 文件: {cookies_path}，请先运行 python -m src.fetchers.twitter_login",
                link=None,
            )
        ]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [
            RawItem(
                source_name=source_name,
                source_type="twitter",
                title="[依赖缺失]",
                content="需要安装 playwright: pip install playwright && playwright install chromium",
                link=None,
            )
        ]

    with open(cookies_file, encoding="utf-8") as f:
        cookies = json.load(f)

    # Playwright 只接受 Strict|Lax|None，Cookie-Editor 导出的值需要规范化
    _same_site_map = {
        "no_restriction": "None",
        "lax": "Lax",
        "strict": "Strict",
        "unspecified": "Lax",
    }
    for c in cookies:
        ss = c.get("sameSite") or ""
        c["sameSite"] = _same_site_map.get(ss.lower(), "Lax")

    items: list[RawItem] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        context.add_cookies(cookies)

        if usernames:
            for username in usernames:
                user_items = _scrape_user_tweets(context, username, source_name, max_tweets)
                items.extend(user_items)
        else:
            items.extend(_scrape_timeline(context, source_name, max_tweets))

        browser.close()

    return items


def _scrape_timeline(context, source_name: str, max_tweets: int) -> list[RawItem]:
    """抓取首页 timeline"""
    page = context.new_page()
    items = []

    try:
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)  # 等待动态内容加载

        items = _extract_tweets_from_page(page, source_name, max_tweets)
    except Exception as e:
        items.append(
            RawItem(
                source_name=source_name,
                source_type="twitter",
                title="[抓取失败]",
                content=f"Timeline 抓取失败: {e}",
                link="https://x.com/home",
            )
        )
    finally:
        page.close()

    return items


def _scrape_user_tweets(context, username: str, source_name: str, max_tweets: int) -> list[RawItem]:
    """抓取指定用户的推文"""
    page = context.new_page()
    items = []
    url = f"https://x.com/{username}"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        items = _extract_tweets_from_page(page, f"{source_name}/{username}", max_tweets)
    except Exception as e:
        items.append(
            RawItem(
                source_name=f"{source_name}/{username}",
                source_type="twitter",
                title="[抓取失败]",
                content=f"用户 @{username} 抓取失败: {e}",
                link=url,
            )
        )
    finally:
        page.close()

    return items


def _extract_tweets_from_page(page, source_name: str, max_tweets: int) -> list[RawItem]:
    """从页面中提取推文内容"""
    items = []

    # 滚动加载更多推文
    for _ in range(3):
        page.mouse.wheel(0, 1500)
        page.wait_for_timeout(1500)

    # 提取推文
    tweet_articles = page.query_selector_all('article[data-testid="tweet"]')

    for article in tweet_articles[:max_tweets]:
        try:
            # 获取用户名
            user_el = article.query_selector('div[data-testid="User-Name"]')
            user_text = user_el.inner_text() if user_el else ""

            # 获取推文内容
            text_el = article.query_selector('div[data-testid="tweetText"]')
            tweet_text = text_el.inner_text() if text_el else ""

            if not tweet_text:
                continue

            # 获取推文链接
            time_el = article.query_selector("time")
            link = None
            if time_el:
                parent_a = time_el.evaluate("el => el.closest('a')?.href")
                if parent_a:
                    link = parent_a

            # 获取时间
            published = time_el.get_attribute("datetime") if time_el else None

            # 用户名取第一行（显示名称）
            display_name = user_text.split("\n")[0] if user_text else "Unknown"

            items.append(
                RawItem(
                    source_name=source_name,
                    source_type="twitter",
                    title=f"@{display_name}",
                    content=tweet_text,
                    link=link,
                    published=published,
                )
            )
        except Exception:
            continue

    return items
