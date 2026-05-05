import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 严格固定 1280x800，确保我们的坐标是准的
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def kill_advertising():
            """强力清理那个 50% Off 的大弹窗"""
            print("执行强制坐标清理广告弹窗...")
            # 根据截图，大弹窗下方的 "I'm fine..." 文本大约在屏幕正中偏下方
            # 坐标 (640, 790) 或 (640, 800) 附近，我们点这个区域
            page.mouse.click(640, 790)
            time.sleep(1)
            # 同时按一下 Esc 键作为保险
            page.keyboard.press("Escape")
            time.sleep(2)

        try:
            # 1. 登录流程
            print("正在登录...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
            
            page.locator('input[type="email"], input[placeholder*="Email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 跳转管理页
            print("正在前往管理页...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # 等待广告蹦出来
            print("等待广告弹窗加载 (8s)...")
            time.sleep(8)
            
            # 3. 强制清理广告
            kill_advertising()

            # 4. 点击 Renew 按钮
            # 既然页面被挡住，我们依然用最稳的坐标点击 Renew 按钮
            # 在 1280x800 且没滚动的情况下，Renew 按钮大约在页面左下方 (260, 750)
            print("点击 Renew 按钮...")
            page.mouse.click(260, 750)
            time.sleep(5)
            
            # 点完之后如果广告又回来了，再点一次清理
            kill_advertising()

            # 5. 启动视频播放
            # 点击视频弹窗的播放三角形 (大约在 640, 430)
            print("尝试点击视频播放...")
            page.mouse.click(640, 430) 
            time.sleep(2)
            
            # 6. 监听领取按钮
            print("开始监听领取按钮...")
            found = False
            for i in range(45): 
                # 寻找包含 Get 和 hour 的按钮
                get_btn = page.locator('button:has-text("Get")').filter(has_text="hour")
                
                if get_btn.is_visible():
                    print("【成功】检测到领取按钮，点击领取！")
                    get_btn.click(force=True)
                    time.sleep(5)
                    page.screenshot(path="success_final.png")
                    found = True
                    break
                
                if i % 5 == 0:
                    # 循环过程中如果广告跳出来，继续坐标清理
                    kill_advertising()
                    print(f"正在等待视频中... ({i*10}s)")
                
                time.sleep(10)
                
            if not found:
                print("超时，保存截图...")
                page.screenshot(path="final_debug.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
