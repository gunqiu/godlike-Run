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

            # 2. 暴力 JS 注入输入 (解决输入框为空的问题)
            print("正在通过 JS 注入账号密码...")
            email = os.environ["GODLIKE_EMAIL"]
            password = os.environ["GODLIKE_PASSWORD"]

            # 这段 JS 会找到输入框，强行赋值并发送“我正在输入”的信号
            js_code = f"""
            (email, pwd) => {{
                const emailInput = document.querySelector('input[type="email"], input[placeholder*="Email"], input[placeholder*="Username"]');
                const pwdInput = document.querySelector('input[type="password"]');
                
                if (emailInput && pwdInput) {{
                    emailInput.value = email;
                    emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    pwdInput.value = pwd;
                    pwdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
                return false;
            }}
            """
            success = page.evaluate(js_code, [email, password])
            
            if success:
                print("JS 注入成功，等待 2 秒确认数据挂载...")
                time.sleep(2)
                page.screenshot(path="debug_js_check.png") # 检查这里框里有没有字
            else:
                print("JS 定位输入框失败。")

            # 3. 点击登录
            print("点击登录按钮...")
            page.locator('button:has-text("Login")').first.click()

            # 4. 检查跳转
            try:
                page.wait_for_url(lambda url: "login" not in url, timeout=15000)
                print("登录成功！")
            except:
                print("登录跳转失败。请检查 debug_js_check.png。")
                # 如果还是空的，尝试最后的物理模拟：
                print("尝试最后的物理模拟点击输入...")
                page.click('input[type="email"]')
                page.keyboard.type(email)
                page.screenshot(path="final_resort_check.png")
                return

            # 5. 后续续期逻辑
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            time.sleep(5)
            page.keyboard.press("Escape") 

            if page.get_by_text("Video will be available in").is_visible():
                print("【跳过】已在冷却。")
                return

            renew_btn = page.get_by_role("button", name="Renew").first
            if renew_btn.is_visible():
                renew_btn.click()
                time.sleep(3)
                page.locator('.fa-play').first.click()
                time.sleep(2)
                page.mouse.click(640, 400) 
                
                for _ in range(40):
                    get_btn = page.get_by_role("button", name="Get +12 Hours")
                    if get_btn.is_visible():
                        get_btn.click()
                        print("【成功】领取完成！")
                        page.screenshot(path="success.png")
                        return
                    time.sleep(10)

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
