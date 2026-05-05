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
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
            
            print("输入凭据...")
            page.locator('input[type="email"], input[placeholder*="Email"]').wait_for(state="visible")
            page.locator('input[type="email"], input[placeholder*="Email"]').click()
            page.keyboard.type(os.environ["GODLIKE_EMAIL"], delay=100)
            page.locator('input[type="password"]').click()
            page.keyboard.type(os.environ["GODLIKE_PASSWORD"], delay=100)
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 前往管理页
            print("正在前往服务器管理页面...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            page.mouse.wheel(0, 500) 
            time.sleep(10) 

            # --- 关键修复：清除促销弹窗 ---
            def clear_popups():
                print("检测并处理干扰弹窗...")
                popups = [
                    "text=I'm fine with waiting in the queue",
                    "svg.fa-times", 
                    "button:has-text('Close')"
                ]
                for selector in popups:
                    try:
                        target = page.locator(selector).first
                        if target.is_visible():
                            target.click(timeout=3000)
                            print(f"已清理弹窗: {selector}")
                            time.sleep(2)
                    except:
                        continue

            # 点 Renew 前清理一次
            clear_popups()

            # 3. 点击 Renew 按钮
            print("执行强制坐标点击 Renew (260, 750)...")
            page.mouse.click(260, 750)
            time.sleep(5) 

            # 点 Renew 后如果又出了广告，再清理一次
            clear_popups()

            # 4. 启动视频播放
            print("尝试启动视频播放...")
            # 点击视频弹窗正中心 (大约 640, 430)
            page.mouse.click(640, 430)
            time.sleep(2)
            
            # 5. 循环监听领取按钮
            print("视频播放中，开始监听领取按钮...")
            found = False
            for i in range(45): # 增加到 450 秒防止超长视频
                get_btn = page.locator('button:has-text("Get")').filter(has_text="hour")
                
                if get_btn.is_visible():
                    print("【成功】检测到领取按钮，正在点击...")
                    get_btn.click(force=True)
                    time.sleep(5)
                    page.screenshot(path="success_final.png")
                    found = True
                    break
                
                if i % 3 == 0:
                    print(f"等待视频结束中... ({i*10}s)")
                time.sleep(10)
                
            if not found:
                print("超时未发现领取按钮，保存截图...")
                page.screenshot(path="timeout_check.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
