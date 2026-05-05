import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. 登录 (略，使用你已经成功的逻辑)
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            # 模拟输入和登录...
            # (这里保持你之前的登录代码不变)
            email_field = page.locator('input[type="email"]')
            pass_field = page.locator('input[type="password"]')
            email_field.fill(os.environ["GODLIKE_EMAIL"])
            pass_field.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 前往服务器管理页
            print("正在前往服务器管理页面...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # 关键：多等一会，让左下角的 Renew 卡片加载出来
            print("等待页面元素加载...")
            time.sleep(8) 

            # 3. 寻找 Renew 按钮 (采用多重定位方案)
            print("寻找 Renew 按钮...")
            
            # 方案 A: 寻找带有 "Renew" 文字且在 "Renew Server" 卡片内的按钮
            # 方案 B: 寻找背景色为蓝色的特定按钮
            # 方案 C: 模糊匹配
            renew_selectors = [
                "div:has-text('Renew Server') >> button:has-text('Renew')", 
                "button:has-text('Renew')",
                "//button[contains(., 'Renew')]",
                "a:has-text('Renew')"
            ]

            target_btn = None
            for selector in renew_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible():
                        target_btn = btn
                        print(f"成功通过选择器找到按钮: {selector}")
                        break
                except:
                    continue

            if target_btn:
                # 如果按钮被遮挡，尝试滚动到它
                target_btn.scroll_into_view_if_needed()
                time.sleep(1)
                
                print("点击 Renew 按钮...")
                # 使用 force=True 强行点击，绕过任何可能的透明遮罩
                target_btn.click(force=True)
                
                # 后面是视频和领取逻辑...
                print("已点击，进入下一步。")
                # (保持后续逻辑)
            else:
                print("【错误】依然找不到按钮。保存当前截图...")
                page.screenshot(path="not_found_debug.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
