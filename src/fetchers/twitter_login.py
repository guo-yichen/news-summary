"""
Twitter 登录辅助脚本 — 手动登录后保存 cookies

使用方法:
    python -m src.fetchers.twitter_login

会打开一个浏览器窗口，你手动登录 Twitter，登录成功后按 Enter 保存 cookies。
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


DEFAULT_COOKIES_PATH = "twitter_cookies.json"


def login_and_save_cookies(cookies_path: str = DEFAULT_COOKIES_PATH):
    """打开浏览器让用户手动登录 Twitter，然后保存 cookies"""
    with sync_playwright() as p:
        # 用系统安装的真实 Chrome，避免被 Twitter 检测为自动化浏览器
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",  # 使用系统 Chrome 而非 Playwright 自带 Chromium
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
        )
        # 移除 webdriver 标记
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        page = context.new_page()

        print("正在打开 Twitter 登录页面...")
        page.goto("https://x.com/login")

        print()
        print("=" * 50)
        print("请在浏览器中手动登录你的 Twitter 账号")
        print("登录成功后（看到首页 timeline），回到终端按 Enter")
        print("=" * 50)
        print()

        input("按 Enter 保存 cookies...")

        # 检查是否登录成功
        cookies = context.cookies()
        auth_cookies = [c for c in cookies if c["name"] in ("auth_token", "ct0")]

        if len(auth_cookies) < 2:
            print("⚠️  看起来还没有登录成功（缺少 auth_token 或 ct0 cookie）")
            print("请确认你已经登录成功，然后再按 Enter 重试")
            input("按 Enter 重新保存...")
            cookies = context.cookies()

        # 保存 cookies
        out_path = Path(cookies_path)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"✅ Cookies 已保存到: {out_path.resolve()}")
        print(f"   共 {len(cookies)} 个 cookie")

        browser.close()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COOKIES_PATH
    login_and_save_cookies(path)
