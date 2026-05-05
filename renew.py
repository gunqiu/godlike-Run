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
            # 1. 登录流程 (保持不变)
            print("正在访问登录页面...")
            page.goto("https://ultra.panel.godlike.host/login", wait_until="networkidle")
            
            login_switch = page.get_by_text("Through Login/Password")
            if login_switch.is_visible():
                login_switch.click(force=True)
            
            print("输入凭据...")
            page.locator('input[type="email"], input[placeholder*="Email"]').wait_for(state="visible")
            page.locator('input[type="email"], input[placeholder*="Email"]').click()
            page.keyboard.type(os.environ["GODLIKE_EMAIL"], delay=100)
            page.locator('input[type="password"]').click()
            page.keyboard.type(os.environ["GODLIKE_PASSWORD"], delay=100)
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            print("登录成功！")

            # 2. 前往管理页
            print("正在前往服务器管理页面...")
            page.goto("https://ultra.panel.godlike.host/server/2a3af930", wait_until="networkidle")
            
            # --- 强化版弹窗清理逻辑 ---
            def force_clear_popups():
                print("深度检测并清除干扰弹窗...")
                # 针对截图中出现的文字和按钮进行多种定位
                selectors = [
                    "text=I'm fine with waiting in the queue",
                    "text=Do you love Godlike?",
                    ".v-overlay__scrim", # 遮罩层
                    "svg.fa-times",       # 右上角关闭图标
                    "button:has-text('Claim -50% Off')" # 虽然不点它，但可以用它辅助判断弹窗存在
                ]
                
                for _ in range(5): # 最多尝试清理 5 次
                    found_popup = False
                    # 优先点击那个灰色的“我愿意排队”文字
                    wait_text = page.get_by_text("I'm fine with waiting in the queue")
                    if wait_text.is_visible():
                        print("发现促销弹窗，点击 'I'm fine with waiting in the queue' 尝试关闭...")
                        wait_text.click(force=True, timeout=5000)
                        found_popup = True
                        time.sleep(2)
                    
                    # 备选：点击 ESC 键
                    page.keyboard.press("Escape")
                    
                    if not found_popup:
                        break
            
            # 页面加载后先清理
            time.sleep(5)
            force_clear_popups()

            # 3. 点击 Renew 按钮
            print("向下滚动并执行 Renew 点击 (260, 750)...")
            page.mouse.wheel(0, 500)
            time.sleep(2)
            page.mouse.click(260, 750)
            time.sleep(5) 

            # 点击后如果又触发了弹窗，再次清理
            force_clear_popups()

            # 4. 启动视频播放
            print("尝试启动视频播放...")
            # 此时应该出现的是 Choose Renewal Method 弹窗
            # 点击视频预览区正中心 (大约 640, 480)
            page.mouse.click(640, 480)
            time.sleep(2)
            
            # 5. 循环监听领取按钮
            print("正在监听领取按钮...")
            found = False
            for i in range(45): 
                # 寻找包含 Get 和 hour 的按钮
                get_btn = page.locator('button:has-text("Get")').filter(has_text="hour")
                
                if get_btn.is_visible():
                    print("【成功】检测到领取按钮，点击领取！")
                    get_btn.click(force=True)
                    time.sleep(5)
                    page.screenshot(path="success_final.png")
                    found = True
                    break
                
                # 如果在等待期间又蹦出了促销弹窗，顺手点掉
                if i % 5 == 0:
                    wait_text = page.get_by_text("I'm fine with waiting in the queue")
                    if wait_text.is_visible():
                        wait_text.click(force=True)
                
                if i % 3 == 0:
                    print(f"等待视频结束中... ({i*10}s)")
                time.sleep(10)
                
            if not found:
                print("未发现领取按钮，保存截图...")
                page.screenshot(path="timeout_check.png")

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="error_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
