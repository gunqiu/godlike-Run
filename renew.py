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

        # --- 核心黑科技：定义自动清理函数 ---
        def auto_clean():
            """这个函数会尝试清理页面上目前可见的所有干扰项"""
            # 1. 中间的大弹窗 (通过文字关闭)
            try:
                # 尝试点击 'I'm fine with waiting'
                target = page.get_by_text("I'm fine with waiting in the queue").first
                if target.is_visible():
                    target.click(force=True, timeout=1000)
                    print("已自动清理：50% Off 大弹窗")
            except: pass

            # 2. 左下角的问卷/反馈弹窗 (通过右上角的 X 关闭)
            try:
                # 寻找问卷弹窗里的关闭图标
                close_icon = page.locator(".v-card").filter(has_text="recommend us").locator(".fa-times, svg").first
                if close_icon.is_visible():
                    close_icon.click(force=True, timeout=1000)
                    print("已自动清理：左下角问卷弹窗")
            except: pass

            # 3. 万能 Escape 键
            page.keyboard.press("Escape")

        try:
            # 1. 登录 (保持不变)
            print("正在登录...")
            page.goto("https://ultra.panel.godlike.host/login")
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible(): login_switch.click(force=True)
            page.locator('input[type="email"]').fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 跳转到管理页
            print("正在前往管理页，准备处理异步弹窗...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930")
            
            # 关键：这里等 8 秒，让所有讨厌的弹窗都蹦出来
            print("等待弹窗完全加载 (8s)...")
            time.sleep(8)
            auto_clean() # 执行第一次深度清理

            # 3. 点击 Renew 按钮
            print("执行 Renew 点击 (260, 750)...")
            page.mouse.wheel(0, 500)
            time.sleep(2)
            page.mouse.click(260, 750)
            
            # 点击 Renew 后可能又会触发弹窗，再等 3 秒清理一次
            time.sleep(3)
            auto_clean()

            # 4. 启动视频播放
            # 此时广告应该清理干净了，点击视频弹窗中心
            print("点击视频播放图标...")
            page.mouse.click(640, 450)
            time.sleep(2)
            
            # 5. 循环监听领取按钮
            print("正在监听视频结束和领取按钮...")
            found = False
            for i in range(45): 
                # 寻找包含 Get 和 hour 的按钮
                get_btn = page.locator('button:has-text("Get")').filter(has_text="hour")
                
                if get_btn.is_visible():
                    print("【成功】检测到领取按钮，正在点击！")
                    get_btn.click(force=True)
                    time.sleep(5)
                    page.screenshot(path="success_final.png")
                    found = True
                    break
                
                # 期间如果弹窗又回来了，自动清理
                if i % 3 == 0: 
                    auto_clean()
                    print(f"等待中... ({i*10}s)")
                
                time.sleep(10)
                
            if not found:
                print("超时未完成，保存当前状态截图...")
                page.screenshot(path="final_debug.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
