import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 严格锁定视口大小，确保坐标精确
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. 登录流程 (保持你原本稳健的逻辑)
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
            
            # 关键：先向下滚动，确保 Renew 区域被加载并进入视野
            print("向下滚动页面并等待渲染...")
            page.mouse.wheel(0, 500) 
            time.sleep(10) 

            # 3. 强制坐标点击 Renew 按钮
            # 根据你的截图 1280x800 布局，Renew 按钮中心点大约在 (260, 750)
            print("执行强制坐标点击 (260, 750)...")
            page.mouse.click(260, 750)
            time.sleep(5) 

            # 4. 点击播放弹窗中的三角形
            print("尝试启动视频播放...")
            # 方案一：点击坐标 (弹窗正中心大约在 640, 480)
            page.mouse.click(640, 480)
            # 方案二：备选点击图标名
            try:
                page.locator(".fa-play").first.click(timeout=3000)
            except:
                pass
            
            # 5. 循环监听领取按钮
            print("视频播放中，开始监听领取按钮...")
            found = False
            for i in range(40): # 最多等 400 秒
                # 模糊匹配包含 "Get" 和 "hour" 的按钮
                get_btn = page.locator('button:has-text("Get")').filter(has_text="hour")
                
                if get_btn.is_visible():
                    print("【成功】检测到领取按钮，正在领取...")
                    get_btn.click(force=True)
                    time.sleep(5)
                    page.screenshot(path="success_final.png")
                    found = True
                    break
                
                if i % 3 == 0:
                    print(f"等待视频结束中... ({i*10}s)")
                time.sleep(10)
                
            if not found:
                print("超时未发现领取按钮，保存截图查原因")
                page.screenshot(path="timeout_check.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
