import os
import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 设置更真实的 User-Agent
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. 访问并选择登录方式 (针对 1 号图)
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            # 精确锁定下方那个“Through Login/Password”文字进行点击
            # 使用 nth(0) 或强制点击确保穿透遮罩
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                print("检测到切换按钮，正在点击进入密码登录模式...")
                login_switch.click(force=True)
                time.sleep(2) # 给 1 秒切换动画时间
            else:
                print("未直接看到切换按钮，尝试点击页面中心坐标强制触发...")
                page.mouse.click(640, 680) # 对应图中红箭头的大概位置

            # 2. 输入账号密码 (针对 2 号图)
            print("正在检查输入框是否出现...")
            # 增加等待输入框出现的逻辑
            email_input = page.locator('input[type="email"]')
            try:
                email_input.wait_for(state="visible", timeout=10000)
                print("输入框已就绪，开始填写信息...")
                email_input.fill(os.environ["GODLIKE_EMAIL"])
                page.fill('input[type="password"]', os.environ["GODLIKE_PASSWORD"])
                
                # 点击下方的蓝按钮 Login
                page.get_by_role("button", name="Login").click()
                print("已提交登录信息。")
            except:
                print("错误：切换到密码登录模式失败，输入框未显示。")
                page.screenshot(path="fail_switch_to_password.png")
                return

            # 3. 验证登录跳转
            try:
                page.wait_for_url(lambda url: "login" not in url, timeout=15000)
                print("登录成功，进入控制面板。")
            except:
                print("登录后未发生跳转，请检查账号密码或是否被拦截。")
                page.screenshot(path="fail_after_login_click.png")
                return

            # 4. 跳转至续期页面
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            time.sleep(5) # 等待 3 号图的广告弹窗
            
            # 按 ESC 键关闭所有潜在弹窗
            page.keyboard.press("Escape")

            # 5. 续期逻辑 (同前)
            if page.get_by_text("Video will be available in").is_visible():
                print("服务器还在冷却期，任务结束。")
                return

            renew_btn = page.locator('button:has-text("Renew")').first
            if renew_btn.is_visible():
                renew_btn.click()
                print("点击 Renew...")
                time.sleep(3)
                
                # 触发视频播放
                page.locator('.fa-play').first.click()
                time.sleep(2)
                page.mouse.click(640, 400) # 点击视频中心开始
                
                print("监测领取按钮中 (最长等待 350秒)...")
                # 循环检测
                for _ in range(35):
                    get_btn = page.get_by_role("button", name="Get +12 Hours")
                    if get_btn.is_visible():
                        get_btn.click()
                        print("【成功】已领取续期时间！")
                        time.sleep(3)
                        page.screenshot(path="success_final.png")
                        return
                    time.sleep(10)
            else:
                print("未找到续期按钮，页面内容如下：")
                page.screenshot(path="error_page_content.png")

        except Exception as e:
            print(f"脚本执行异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
