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

        def kill_advertising():
            """清理广告和问卷干扰"""
            print("正在执行清障操作...")
            # 1. 坐标点击关闭 50% 折扣大弹窗 (针对 I'm fine... 文本位置)
            page.mouse.click(640, 790)
            # 2. 尝试点击左下角问卷的关闭 X
            try:
                survey_close = page.locator(".v-card").filter(has_text="recommend us").locator(".fa-times, svg").first
                if survey_close.is_visible():
                    survey_close.click(force=True, timeout=1000)
            except: pass
            # 3. 按 Esc 保险
            page.keyboard.press("Escape")
            time.sleep(2)

        try:
            # 1. 登录流程 (保持稳定版本)
            print("正在登录...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
            
            page.locator('input[type="email"], input[placeholder*="Email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 跳转管理页
            print("正在前往管理页...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            print("等待干扰项加载 (8s)...")
            time.sleep(8)
            kill_advertising()

            # 3. 精准滚动并点击 Renew
            print("向下微调滚动位置...")
            # 滚动 250 像素正好能让底部的 Renew Server 模块完整显示
            page.mouse.wheel(0, 250)
            time.sleep(3)
            
            # 此时 Renew 按钮应该在视野内了，我们用 selector 结合 force 点击
            print("尝试点击 Renew 按钮...")
            renew_btn = page.locator('button:has-text("Renew")').first
            # 如果 selector 失败，用备选坐标 (260, 750) 
            try:
                renew_btn.click(force=True, timeout=5000)
                print("通过元素成功点击 Renew")
            except:
                print("元素点击失败，尝试坐标点击 (260, 750)...")
                page.mouse.click(260, 750)
            
            time.sleep(5)
            # 如果点完 Renew 又弹广告，再清一次
            kill_advertising()

            # 4. 启动视频播放
            print("点击视频预览启动播放...")
            # 视频弹窗中心坐标
            page.mouse.click(640, 430) 
            time.sleep(2)
            
            # 5. 监听领取按钮
            print("开始监听视频结束和领取按钮...")
            found = False
            for i in range(45): 
                get_btn = page.locator('button:has-text("Get")').filter(has_text="hour")
                
                if get_btn.is_visible():
                    print("【成功】检测到领取按钮，点击领取！")
                    get_btn.click(force=True)
                    time.sleep(5)
                    page.screenshot(path="success_final.png")
                    found = True
                    break
                
                if i % 4 == 0:
                    kill_advertising() # 防止视频中途跳广告
                    print(f"正在等待中... ({i*10}s)")
                time.sleep(10)
                
            if not found:
                print("超时未发现领取按钮，请检查截图 final_debug.png")
                page.screenshot(path="final_debug.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
