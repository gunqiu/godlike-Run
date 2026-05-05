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
            # 1. 登录流程 (保持不变)
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
            
            email_field = page.locator('input[type="email"], input[placeholder*="Email"]')
            pass_field = page.locator('input[type="password"]')
            email_field.wait_for(state="visible")
            email_field.click()
            page.keyboard.type(os.environ["GODLIKE_EMAIL"], delay=100)
            pass_field.click()
            page.keyboard.type(os.environ["GODLIKE_PASSWORD"], delay=100)
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 前往管理页并点击 Renew
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            time.sleep(10)
            
            print("寻找并点击 Renew 按钮...")
            renew_btn = page.locator('button:has-text("Renew")').first
            renew_btn.click(force=True)
            time.sleep(5) # 等待弹窗弹出

            # 3. 点击播放视频 (白色三角形)
            print("检测到播放弹窗，正在准备点击播放...")
            # 方案 A: 点击播放图标
            play_icon = page.locator(".fa-play").first
            if play_icon.is_visible():
                play_icon.click()
                print("已点击播放图标")
            else:
                # 方案 B: 直接点击弹窗中心位置 (根据截图，大约是屏幕中心)
                print("未找到图标，尝试点击弹窗中心...")
                page.mouse.click(640, 500) 
            
            # 4. 等待视频播放结束
            # 视频通常在 30s 到 120s 之间，我们采取循环监听按钮的方式
            print("等待视频播放完成，正在监听领取按钮...")
            
            found_get_button = False
            # 循环 30 次，每次等 10 秒，总计 300 秒（5分钟）
            for i in range(30):
                # 寻找 "Get +24 hours" 或类似的领取按钮
                get_btn = page.get_by_role("button").filter(has_text="Get +24 hours")
                
                if get_btn.is_visible():
                    print(f"【成功】看到领取按钮了！正在点击...")
                    get_btn.click(force=True)
                    found_get_button = True
                    time.sleep(5)
                    page.screenshot(path="success_renew.png")
                    print("续期操作全部完成！")
                    break
                
                if i % 3 == 0:
                    print(f"仍在等待中... ({i*10}秒)")
                time.sleep(10)

            if not found_get_button:
                print("超时：未能看到领取按钮，请检查截图。")
                page.screenshot(path="timeout_video.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
