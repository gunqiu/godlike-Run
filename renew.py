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

        def kill_advertising():
            """清理广告和问卷"""
            print("执行清障...")
            # 关闭 50% 折扣 (根据截图文字位置)
            page.mouse.click(640, 790)
            # 关闭左下角问卷
            try:
                survey_close = page.locator(".v-card").filter(has_text="recommend us").locator(".fa-times, svg").first
                if survey_close.is_visible():
                    survey_close.click(force=True, timeout=1000)
            except: pass
            page.keyboard.press("Escape")
            time.sleep(1)

        try:
            # 1. 登录 (保持之前成功的逻辑)
            print("正在登录...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible(): login_switch.click(force=True)
            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 跳转管理页
            print("正在前往管理页...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # 等待广告出现并清理
            time.sleep(8)
            kill_advertising()

            # 3. 定位并点击 Renew 按钮
            print("定位 Renew 按钮...")
            # 使用包含 'Renew' 文字的按钮，通常它是在 server__renew-block 里的
            renew_btn = page.locator('button:has-text("Renew")').first
            
            # 重要：自动滚动到按钮可见的位置，不使用固定的像素值
            renew_btn.scroll_into_view_if_needed()
            time.sleep(2)
            
            # 强制点击
            print("点击 Renew...")
            renew_btn.click(force=True)
            
            time.sleep(5)
            kill_advertising()

            # 4. 启动视频播放
            print("点击视频播放...")
            # 点击视频弹窗区域
            page.mouse.click(640, 430) 
            time.sleep(2)
            
            # 5. 监听领取按钮
            print("监听领取按钮中...")
            found = False
            for i in range(45): 
                get_btn = page.locator('button:has-text("Get")').filter(has_text="hour")
                
                if get_btn.is_visible():
                    print("【成功】检测到领取按钮！")
                    get_btn.click(force=True)
                    time.sleep(5)
                    page.screenshot(path="success_final.png")
                    found = True
                    break
                
                if i % 4 == 0:
                    kill_advertising()
                    print(f"等待中... ({i*10}s)")
                time.sleep(10)
                
            if not found:
                page.screenshot(path="final_debug.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
