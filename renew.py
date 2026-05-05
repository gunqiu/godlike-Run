import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            # 1. 登录流程
            page.goto("https://ultra.panel.godlike.host/login")
            page.click("text=Through Login/Password")
            page.fill('input[type="email"]', os.environ["GODLIKE_EMAIL"])
            page.fill('input[type="password"]', os.environ["GODLIKE_PASSWORD"])
            page.click('button:has-text("Login")')
            
            # 2. 跳转到服务器页面
            page.goto("https://ultra.panel.godlike.host/server/2a3af930")
            page.wait_for_timeout(5000) # 等待4-5秒让弹窗加载

            # 3. 处理图3的广告弹窗 (如果有)
            close_button = page.locator('button i.fa-times').first # 或者是图中的 X 按钮
            if close_button.is_visible():
                close_button.click()
                print("已关闭初始广告弹窗")

            # 4. 判断续期状态
            # 检查是否有黄色倒计时文字 "Video will be available in"
            cooldown_text = page.locator('text=Video will be available in')
            if cooldown_text.is_visible():
                print("服务器处于冷却期，无需续期。")
                page.screenshot(path="cooldown_status.png")
                return

            # 5. 执行续期流程 (图5)
            renew_btn = page.locator('button:has-text("Renew")')
            if renew_btn.is_visible():
                renew_btn.click()
                print("点击了 Renew 按钮")
                
                # 点击中间的播放占位符 (图6)
                page.wait_for_selector('.fa-play', timeout=10000)
                page.click('.fa-play')
                
                # 点击 YouTube 内部的播放按钮 (图7, 图8)
                # 注意：YouTube 视频通常在 iframe 里
                page.wait_for_timeout(3000)
                # 尝试通过点击页面中心来触发播放
                page.mouse.click(640, 400) 
                
                print("开始观看视频，等待 300 秒...")
                # 等待进度条跑完
                time.sleep(300) 

                # 6. 领取时间 (图9)
                get_hours_btn = page.locator('button:has-text("Get +12 Hours")')
                if get_hours_btn.is_visible():
                    get_hours_btn.click()
                    print("续期成功：已点击 Get +12 Hours")
                    page.wait_for_timeout(5000)
                    page.screenshot(path="success_renew.png")
                else:
                    print("未检测到领取按钮，可能时间未到。")
                    page.screenshot(path="error_no_get_button.png")
            else:
                print("未找到 Renew 按钮，可能页面加载异常。")
                page.screenshot(path="error_no_renew_btn.png")

        except Exception as e:
            print(f"工作流出现异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
