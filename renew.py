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

        def auto_clean():
            """清理干扰弹窗"""
            try:
                target = page.get_by_text("I'm fine with waiting in the queue").first
                if target.is_visible():
                    target.click(force=True, timeout=2000)
                    print("已清理：50% Off 弹窗")
            except: pass

            try:
                survey_close = page.locator(".v-card").filter(has_text="recommend us").locator(".fa-times, svg").first
                if survey_close.is_visible():
                    survey_close.click(force=True, timeout=2000)
                    print("已清理：左下角问卷")
            except: pass
            page.keyboard.press("Escape")

        try:
            # 1. 登录流程
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
            
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

            # 2. 跳转管理页
            print("正在前往管理页...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            print("等待异步干扰弹窗出现并清理 (8s)...")
            time.sleep(8)
            auto_clean()

            # 3. 自动对齐并点击 Renew 按钮
            print("定位 Renew 按钮并自动滚动对齐...")
            # 使用更精准的选择器定位那个 Renew 按钮
            renew_btn = page.locator('button.server__renew-block__button').first
            
            # 核心改进：自动滚动到按钮可见的位置，而不是盲目向下滚 500
            renew_btn.scroll_into_view_if_needed()
            time.sleep(2)
            
            # 使用 force=True 强制点击按钮本身，不再依赖坐标
            renew_btn.click(force=True)
            print("已点击 Renew 按钮")
            
            time.sleep(4)
            auto_clean()

            # 4. 启动视频播放
            # 弹窗出现后，直接点击弹窗内的播放图标类名，而不是点屏幕中心
            print("尝试点击视频播放图标...")
            play_icon = page.locator(".fa-play").first
            if play_icon.is_visible():
                play_icon.click(force=True)
            else:
                # 如果找不到图标，再尝试点击弹窗的大概位置
                page.mouse.click(640, 400) 
            
            # 5. 监听领取按钮
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
                
                if i % 3 == 0: 
                    auto_clean()
                    print(f"正在等待视频结束... ({i*10}s)")
                time.sleep(10)
                
            if not found:
                print("超时未发现领取按钮")
                page.screenshot(path="final_debug.png")

        except Exception as e:
            print(f"脚本执行异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
