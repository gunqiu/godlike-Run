import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # 模拟真实浏览器，避免被识别为机器人
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. 登录流程
            print("正在登录...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            # 点击 "Through Login/Password"
            login_tab = page.get_by_text("Through Login/Password")
            if login_tab.is_visible():
                login_tab.click()
            
            page.fill('input[type="email"]', os.environ["GODLIKE_EMAIL"])
            page.fill('input[type="password"]', os.environ["GODLIKE_PASSWORD"])
            page.click('button:has-text("Login")')
            page.wait_for_load_state("networkidle")

            # 2. 跳转到目标服务器页面
            print("跳转到服务器管理页面...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # 强制等待5秒处理潜在弹窗 (图3)
            time.sleep(5)
            # 尝试通过点击页面空白处或特定的 X 按钮来关掉弹窗
            page.mouse.click(10, 10) 

            # 3. 核心状态判断
            # 检查是否有黄色倒计时 (图4)
            cooldown = page.locator('div:has-text("Video will be available in")').last
            if cooldown.is_visible():
                print("【跳过】服务器处于冷却期，无需续期。")
                page.screenshot(path="status_cooldown.png", full_page=True)
                return

            # 4. 寻找 Renew 按钮 (图5)
            # 使用更宽泛的定位方式防止按钮文本变化
            renew_btn = page.locator('button:has-text("Renew")').first
            if not renew_btn.is_visible():
                print("【错误】未找到 Renew 按钮，截图保存。")
                page.screenshot(path="error_no_renew_btn.png", full_page=True)
                return

            print("点击 Renew 续期按钮...")
            renew_btn.click()
            time.sleep(3)

            # 5. 处理视频播放 (图6 & 图7)
            print("寻找播放按钮...")
            # 尝试点击中间的大三角形 (可能是 Canvas 或特定类名)
            play_overlay = page.locator('.fa-play').first
            if play_overlay.is_visible():
                play_overlay.click()
            
            # 针对 YouTube 视频的二次点击确保开始 (图7)
            time.sleep(2)
            page.mouse.click(640, 400) # 点击视频中心

            # 6. 循环检测进度与领取按钮 (图9)
            print("开始监测进度条，预计等待 240-300 秒...")
            start_time = time.time()
            found_get = False
            
            # 最多等待 8 分钟 (480秒)
            while time.time() - start_time < 480:
                # 检查 "Get +12 Hours" 按钮
                get_btn = page.locator('button:has-text("Get +12 Hours")')
                if get_btn.is_visible():
                    print("检测到领取按钮！点击领取...")
                    get_btn.click()
                    found_get = True
                    time.sleep(5)
                    page.screenshot(path="success_done.png", full_page=True)
                    break
                
                # 每15秒截图一次查看进度 (可选)
                if int(time.time() - start_time) % 60 == 0:
                    print(f"仍在播放中... 已等待 {int(time.time() - start_time)} 秒")
                
                time.sleep(5)

            if not found_get:
                print("【失败】超过时间仍未出现领取按钮。")
                page.screenshot(path="error_timeout.png", full_page=True)

        except Exception as e:
            print(f"【异常】发生错误: {str(e)}")
            page.screenshot(path="error_exception.png", full_page=True)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
