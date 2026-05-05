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
            # 1. 登录流程 (沿用你已经跑通的代码)
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

            try:
                page.wait_for_url(lambda url: "login" not in url, timeout=15000)
                print("登录成功！")
            except:
                print("登录跳转失败。")
                return

            # 2. 进入服务器管理页
            print("正在前往服务器管理页面...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # --- 关键：处理促销弹窗 ---
            print("检测并处理干扰弹窗...")
            time.sleep(5) # 等待弹窗完全弹出
            
            # 方案 A: 尝试按 ESC 键关闭
            page.keyboard.press("Escape")
            
            # 方案 B: 精准点击弹窗上的“关闭”文字或 X 按钮
            close_selectors = [
                "text=I'm fine with waiting in the queue", # 图片底部的文字
                "svg.fa-times",                            # 右上角的 X
                ".modal-close", 
                "button:has-text('Close')"
            ]
            
            for selector in close_selectors:
                try:
                    target = page.locator(selector).first
                    if target.is_visible():
                        target.click(timeout=3000)
                        print(f"已通过 {selector} 关闭弹窗")
                        time.sleep(2)
                except:
                    continue

            # 3. 寻找 Renew 按钮
            print("寻找 Renew 按钮...")
            renew_btn = page.locator('button:has-text("Renew")').first
            
            if renew_btn.is_visible():
                # 检查是否处于冷却期
                if page.get_by_text("Video will be available in").is_visible():
                    print("【跳过】已在冷却期，无需续期。")
                    return
                
                print("点击 Renew 按钮...")
                renew_btn.click(force=True) # 强制点击，防止还有残余遮罩
                time.sleep(5)
                
                # 4. 视频流程
                print("开始视频流程...")
                # 尝试点击播放图标
                play_icon = page.locator(".fa-play").first
                if play_icon.is_visible():
                    play_icon.click()
                    time.sleep(2)
                
                # 点击视频区域中心确保播放
                page.mouse.click(640, 480)
                
                # 5. 循环检测领取按钮
                print("等待领取按钮出现 (最长 400 秒)...")
                for i in range(40):
                    get_btn = page.get_by_role("button", name="Get +12 Hours")
                    if get_btn.is_visible():
                        get_btn.click()
                        print("【成功】续期领到！")
                        page.screenshot(path="success_final.png")
                        return
                    time.sleep(10)
                
                print("超时：未看到领取按钮。")
                page.screenshot(path="error_no_get_button.png")
            else:
                print("未找到 Renew 按钮，请检查截图确认页面状态。")
                page.screenshot(path="error_no_renew_btn.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
