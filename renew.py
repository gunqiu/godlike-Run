import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 严格锁定 1280x800 分辨率
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def kill_advertising():
            """强力清理弹窗：坐标点击右上角 X"""
            print("正在执行强力清障 (点击右上角 X)...")
            
            # 1. 点击 50% Off 弹窗右上角的 X (根据 1280x800 比例计算)
            # 这个 X 大约在横坐标 730，纵坐标 155 左右
            page.mouse.click(735, 155)
            time.sleep(1)
            
            # 2. 点击底部的 "I'm fine..." 作为备选
            page.mouse.click(640, 790)
            
            # 3. 按下键盘 Esc
            page.keyboard.press("Escape")
            time.sleep(2)
            
            # 4. 清理左下角小问卷 (如果存在)
            try:
                page.locator(".v-card").filter(has_text="recommend us").locator(".fa-times, svg").first.click(force=True, timeout=500)
            except: pass

        try:
            # 1. 登录
            print("正在登录...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible(): login_switch.click(force=True)
            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 前往管理页
            print("前往管理页...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # 给弹窗充足的弹出时间
            print("等待广告弹窗 (10s)...")
            time.sleep(10)
            
            # 执行清障
            kill_advertising()

            # 3. 寻找 Renew 按钮 (不滚动，让它自动找)
            print("点击 Renew 按钮...")
            renew_btn = page.locator('button:has-text("Renew")').first
            # 自动对齐
            renew_btn.scroll_into_view_if_needed()
            time.sleep(1)
            # 点击
            renew_btn.click(force=True)
            print("已点击 Renew")
            
            time.sleep(5)
            kill_advertising() # 弹窗可能再次出现

            # 4. 视频播放
            print("启动视频播放...")
            page.mouse.click(640, 430) 
            time.sleep(2)
            
            # 5. 监听领取
            print("开始监听领取按钮...")
            found = False
            for i in range(45): 
                get_btn = page.locator('button:has-text("Get")').filter(has_text="hour")
                
                if get_btn.is_visible():
                    print("【成功】检测到领取按钮，点击！")
                    get_btn.click(force=True)
                    time.sleep(5)
                    page.screenshot(path="success_final.png")
                    found = True
                    break
                
                if i % 4 == 0:
                    kill_advertising()
                    print(f"等待视频中... ({i*10}s)")
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
