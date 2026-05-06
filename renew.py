import os
import time
from playwright.sync_api import sync_playwright

# 配置信息
HOME_URL = "https://godlike.host/"
LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"

def run():
    with sync_playwright() as p:
        # 尝试使用更“像人”的启动参数
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ])
        
        # 深度伪装 Context
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        # 注入脚本，抹除自动化痕迹
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()

        def clear_popups():
            """强力清理所有妨碍点击的弹窗"""
            try:
                page.evaluate("""() => {
                    const selectors = ['[class*="modal"]', '[class*="dialog"]', 'iframe[title*="chat"]', '.fixed.bottom-4', '[id*="hubspot"]'];
                    selectors.forEach(s => document.querySelectorAll(s).forEach(el => el.remove()));
                }""")
            except: pass

        # --- 步骤 1: 登录 (带重试和伪装) ---
        print("\n" + "="*40 + "\n步骤 1: 执行登录 (尝试绕过检测)")
        try:
            # 策略：先去主页，再跳登录页，模拟真实访问路径
            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            
            # 等待邮箱输入框
            email_field = page.locator('input[type="email"]').first
            email_field.wait_for(state="visible", timeout=60000)
            
            # 模拟人工输入速度
            email_field.type(os.environ["GODLIKE_EMAIL"], delay=100)
            page.locator('input[type="password"]').first.type(os.environ["GODLIKE_PASSWORD"], delay=100)
            
            # 点击登录按钮
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=30000)
            print("✅ 登录成功")
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            page.screenshot(path="LOGIN_FAIL.png")
            browser.close()
            return

        # --- 步骤 2: 点击 Renew (核心战场) ---
        print("\n" + "="*40 + "\n步骤 2: 点击 1 号图 Renew")
        page.goto(SERVER_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(15) 
        
        clear_popups()
        page.keyboard.press("Escape")
        
        # 查找按钮并强行点击
        btn = page.locator('button:has-text("Renew"), a:has-text("Renew"), [role="button"]:has-text("Renew")').first
        if btn.is_visible():
            btn.click(force=True)
            print("✅ 已点击 Renew 按钮")
        else:
            print("⚠️ 未发现按钮标签，尝试坐标保底点击 (240, 485)")
            page.mouse.click(240, 485)
        time.sleep(8)

        # --- 步骤 3 & 4: 播放视频 ---
        print("\n" + "="*40 + "\n步骤 3 & 4: 启动 2、3 号图播放逻辑")
        clear_popups()
        # 点击屏幕中央激活可能存在的弹窗播放
        page.mouse.click(640, 400) 
        time.sleep(5)
        # 尝试点 YouTube 按钮
        for frame in page.frames:
            if "youtube" in frame.url:
                try:
                    frame.locator(".ytp-large-play-button").click(force=True, timeout=5000)
                    print("✅ 已点击视频内播放按钮")
                except: pass
        
        # --- 步骤 5: 领取奖励 ---
        print("\n" + "="*40 + "\n步骤 5: 等待 4 号图奖励")
        start = time.time()
        while time.time() - start < 540:
            if int(time.time() - start) % 60 == 0:
                print(f"等待中: {int(time.time() - start)} 秒...")
                clear_popups()
                page.keyboard.press("Escape")

            if "Get +12 Hours" in page.content():
                print("🎉 发现奖励按钮！执行领取")
                page.get_by_text("Get +12 Hours").first.click(force=True)
                print("✨ 任务圆满完成！")
                time.sleep(5)
                browser.close()
                return
            time.sleep(10)

        print("❌ 最终超时")
        page.screenshot(path="FINAL_TIMEOUT.png")
        browser.close()

if __name__ == "__main__":
    run()
