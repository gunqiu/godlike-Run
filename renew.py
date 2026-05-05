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
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            # 1. 切换到密码模式
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
                time.sleep(2)

            # 2. 精准账号密码输入
            print("开始精准输入凭据...")
            email = os.environ["GODLIKE_EMAIL"]
            password = os.environ["GODLIKE_PASSWORD"]

            # 使用更宽泛但排他的 CSS 选择器
            # 账号框通常是第一个 input，或者是 type 为 text/email 的那个
            email_input = page.locator('input:not([type="password"]):not([type="hidden"])').first
            pwd_input = page.locator('input[type="password"]')

            # 先清空，再慢速打字
            email_input.click()
            # 强制清空旧内容
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(email, delay=150)
            
            pwd_input.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(password, delay=150)

            # 截图验证
            page.screenshot(path="double_check_input.png")

            # 3. 点击登录
            print("点击登录按钮...")
            # 有时按钮也是动态的，我们直接按回车
            page.keyboard.press("Enter")

            # 4. 检查跳转
            try:
                page.wait_for_url(lambda url: "login" not in url, timeout=15000)
                print("登录成功！")
            except:
                print("登录跳转失败，正在尝试备用点击方案...")
                # 备用方案：如果回车没用，点那个明显的蓝色按钮
                page.locator('button', has_text="Login").click()
                time.sleep(5)
                if "login" in page.url:
                    page.screenshot(path="final_fail.png")
                    return

            # 5. 后续续期逻辑
            print("访问续期页面...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            time.sleep(5)
            page.keyboard.press("Escape") 

            # 检测 Renew 按钮
            renew_btn = page.locator('button:has-text("Renew")').first
            if renew_btn.is_visible():
                renew_btn.click()
                print("开始观看视频...")
                time.sleep(5)
                # 强制点击视频区域中心
                page.mouse.click(640, 450)
                
                print("循环检测领取按钮...")
                for _ in range(45):
                    get_btn = page.get_by_role("button", name="Get +12 Hours")
                    if get_btn.is_visible():
                        get_btn.click()
                        print("【成功】领取完成！")
                        page.screenshot(path="success_final.png")
                        return
                    time.sleep(10)
            else:
                print("未发现续期按钮，可能已续期或页面加载未完成。")

        except Exception as e:
            print(f"异常: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
