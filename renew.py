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
            # 1. 访问登录页
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            # 2. 切换到密码模式 (1号图 -> 2号图)
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
                time.sleep(2)

            # 3. 强力输入账号密码 (模拟真人按键)
            print("正在模拟真人输入凭据...")
            email_field = page.locator('input[type="email"], input[placeholder*="Email"], input[placeholder*="Username"]')
            pass_field = page.locator('input[type="password"]')
            
            # 确保输入框可见
            email_field.wait_for(state="visible", timeout=10000)
            
            # 点击并清空，然后逐字输入
            email_field.click()
            page.keyboard.type(os.environ["GODLIKE_EMAIL"], delay=100) # 每个字母间隔100毫秒
            
            pass_field.click()
            page.keyboard.type(os.environ["GODLIKE_PASSWORD"], delay=100)
            
            # 此时截个图，确认字有没有打进去 (调试用)
            page.screenshot(path="debug_typing_check.png")

            # 4. 提交登录
            print("点击登录按钮...")
            # 尝试定位那个蓝色的 Login 按钮
            login_btn = page.locator('button:has-text("Login")').first
            login_btn.click()

            # 5. 等待跳转
            try:
                # 如果 15 秒内没跳转，说明账号密码错或有验证码
                page.wait_for_url(lambda url: "login" not in url, timeout=15000)
                print("登录成功！")
            except:
                print("登录跳转失败。请查看 debug_typing_check.png 确认账号密码是否输入。")
                page.screenshot(path="fail_after_submit.png")
                return

            # 6. 后续续期逻辑 (保持不变)
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            time.sleep(5)
            page.keyboard.press("Escape") # 关弹窗

            # 检查冷却 (4号图)
            if page.get_by_text("Video will be available in").is_visible():
                print("【跳过】已在冷却期。")
                return

            # 寻找并点击 Renew (5号图)
            renew_btn = page.get_by_role("button", name="Renew").first
            if renew_btn.is_visible():
                renew_btn.click()
                print("开始视频流程...")
                time.sleep(3)
                # 播放视频 (6, 7, 8号图)
                page.locator('.fa-play').first.click()
                time.sleep(2)
                page.mouse.click(640, 400) 
                
                # 循环领取 (9号图)
                for _ in range(40):
                    get_btn = page.get_by_role("button", name="Get +12 Hours")
                    if get_btn.is_visible():
                        get_btn.click()
                        print("【成功】续期领到！")
                        page.screenshot(path="success.png")
                        return
                    time.sleep(10)
            else:
                print("未找到 Renew 按钮。")
                page.screenshot(path="error_final_state.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
