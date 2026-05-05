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
            # --- 保持你之前完全正确的登录代码 ---
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
                time.sleep(2)

            print("正在模拟真人输入凭据...")
            email_field = page.locator('input[type="email"], input[placeholder*="Email"], input[placeholder*="Username"]')
            pass_field = page.locator('input[type="password"]')
            email_field.wait_for(state="visible", timeout=10000)
            
            email_field.click()
            page.keyboard.type(os.environ["GODLIKE_EMAIL"], delay=100)
            pass_field.click()
            page.keyboard.type(os.environ["GODLIKE_PASSWORD"], delay=100)
            
            print("点击登录按钮...")
            page.locator('button:has-text("Login")').first.click()

            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")
            # --- 登录部分结束 ---

            # 2. 进入管理页
            print("正在前往服务器管理页面...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # 这里多等几秒，确保左下角的卡片加载出来
            time.sleep(10) 

            # 3. 寻找 Renew 按钮 (尝试更精准的卡片定位)
            print("寻找 Renew 按钮...")
            
            # 这里的逻辑是：先找包含 "Renew Server" 文字的那个方框，再找里面的按钮
            # 这样可以避开页面其他地方可能出现的干扰
            renew_section = page.locator('div:has-text("Renew Server")').last
            renew_btn = renew_section.locator('button:has-text("Renew")').first

            if renew_btn.is_visible():
                print("找到按钮，尝试点击...")
                renew_btn.scroll_into_view_if_needed()
                time.sleep(1)
                renew_btn.click(force=True) 
                
                # 后面是视频流程...
                print("点击成功，开始后续流程...")
                time.sleep(5)
                # (在此处继续你的视频播放和领取逻辑)
                
            else:
                print("【警告】直接定位失败，尝试全页面搜索...")
                # 备用方案：全页面找那个蓝色的 Renew 按钮
                backup_btn = page.locator('button:has-text("Renew")').first
                if backup_btn.is_visible():
                    backup_btn.click(force=True)
                    print("备用方案点击成功")
                else:
                    print("还是没找到，保存截图分析")
                    page.screenshot(path="not_found_debug.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
