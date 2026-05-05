import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 固定窗口大小，确保坐标一致
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. 登录流程 (保持你原本能成功的逻辑)
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

            # 2. 前往服务器管理页
            print("正在前往服务器管理页面...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # 延长等待时间，确保页面所有卡片加载完毕
            print("等待 12 秒确保元素完全渲染...")
            time.sleep(12) 

            # 3. 寻找 Renew 按钮
            print("寻找 Renew 按钮...")
            
            # 先尝试通过文字匹配 (加上 nth=0 避免干扰)
            renew_btn = page.get_by_role("button").filter(has_text="Renew").first
            
            if renew_btn.is_visible():
                print("通过选择器找到按钮，点击...")
                renew_btn.click(force=True)
            else:
                # --- 核心修复：坐标点击方案 ---
                # 根据图片 error_no_renew_btn_2.jpg，按钮位于左下角
                # 在 1280x800 视口下，该位置大约在 x=260, y=940 (需要向滚动)
                # 或者我们直接让它滚动到底部再点
                print("【切换策略】选择器失效，尝试执行底层坐标点击...")
                page.mouse.wheel(0, 1000) # 向下滚动到底
                time.sleep(2)
                
                # 在 1280x800 的布局中，Renew 按钮中心点大约在 (265, 750) 附近
                print("点击物理坐标 (265, 750)...")
                page.mouse.click(265, 750)
            
            # 4. 检测是否进入了视频页面
            time.sleep(5)
            if "renew" in page.url or page.get_by_text("Video will be available").is_visible():
                print("成功触发续期流程！")
                
                # 这里继续点击播放和领取的逻辑
                # ... (保持之前代码里的视频播放部分)
                
            else:
                print("点击后未检测到页面变化，保存截图...")
                page.screenshot(path="after_click_fail.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
