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

        # --- 核心清理函数：处理 50% 折扣和左下角问卷 ---
        def auto_clean():
            try:
                # 1. 处理中间大弹窗
                target = page.get_by_text("I'm fine with waiting in the queue").first
                if target.is_visible():
                    target.click(force=True, timeout=2000)
                    print("已清理：50% Off 弹窗")
                    time.sleep(1)
            except: pass

            try:
                # 2. 处理左下角调查问卷 (寻找问卷卡片上的关闭按钮)
                survey_close = page.locator(".v-card").filter(has_text="recommend us").locator(".fa-times, svg").first
                if survey_close.is_visible():
                    survey_close.click(force=True, timeout=2000)
                    print("已清理：左下角问卷")
                    time.sleep(1)
            except: pass
            
            # 3. 万能 Esc 键
            page.keyboard.press("Escape")

        try:
            # 1. 登录流程 (接回之前确认有效的逻辑)
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            # 切换到账号密码模式
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
            
            print("输入凭据...")
            # 使用更稳健的选择器并模拟真实打字
            email_input = page.locator('input[type="email"], input[placeholder*="Email"]').first
            email_input.wait_for(state="visible")
            email_input.click()
            page.keyboard.type(os.environ["GODLIKE_EMAIL"], delay=100)
            
            pass_input = page.locator('input[type="password"]').first
            pass_input.click()
            page.keyboard.type(os.environ["GODLIKE_PASSWORD"], delay=100)
            
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 跳转到管理页
            print("正在前往管理页...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # 关键：等待 8 秒让弹窗跳完，然后清理
            print("等待异步干扰弹窗出现并清理 (8s)...")
            time.sleep(8)
            auto_clean()

            # 3. 点击 Renew 按钮
            print("执行 Renew 点击 (260, 750)...")
            page.mouse.wheel(0, 500)
            time.sleep(2)
            page.mouse.click(260, 750)
            
            # 点完 Renew 如果广告重现，再清一次
            time.sleep(4)
            auto_clean()

            # 4. 启动视频播放
            print("尝试点击视频播放区域...")
            page.mouse.click(640, 430) 
            time.sleep(2)
            
            # 5. 循环监听领取按钮
            print("视频播放中，开始监听领取按钮...")
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
                
                # 周期性自动清理新出的干扰
                if i % 3 == 0: 
                    auto_clean()
                    print(f"正在等待视频结束... ({i*10}s)")
                
                time.sleep(10)
                
            if not found:
                print("超时未发现领取按钮，请检查截图 final_debug.png")
                page.screenshot(path="final_debug.png")

        except Exception as e:
            print(f"脚本执行异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
