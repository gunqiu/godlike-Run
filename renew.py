import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def get_body_text():
            try: return page.locator("body").inner_text(timeout=1000)
            except: return ""

        # ── 逻辑 5：处理 5 号图中的特殊窗口（推广弹窗） ────────────────
        def handle_ad_popup():
            """发现 5 号图窗口就点击右上角叉去掉"""
            try:
                # 检测 5 号图特有的文字
                if "Do you love Godlike?" in get_body_text():
                    print("⚠️ 发现 5 号图推广窗口，正在清理...")
                    # 尝试点击右上角的叉号 (通常是 dialog 中的第一个 button)
                    close_btn = page.locator('div[role="dialog"] button:has(svg), .modal-content button').first
                    if close_btn.is_visible():
                        close_btn.click()
                        time.sleep(1)
                    else:
                        page.keyboard.press("Escape")
            except: pass

        # ── 步骤 1 & 2：登录并进入 1 号图页面 ────────────────────────
        def step_prepare():
            print("=" * 50)
            print("步骤 1：登录并前往服务器页面")
            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            try:
                page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
                page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
                page.locator('button:has-text("Login")').first.click()
                page.wait_for_url(lambda url: "login" not in url, timeout=20000)
            except: pass
            
            page.goto(SERVER_URL, wait_until="domcontentloaded")
            time.sleep(5)
            handle_ad_popup()
            print("✅ 已到达 1 号图界面")

        # ── 步骤 3：处理 1 号图点击 Renew ───────────────────────────
        def step_click_renew():
            print("=" * 50)
            print("步骤 2：点击 1 号图中的 Renew 按钮")
            handle_ad_popup()
            # 定位 Renew 按钮
            renew_btn = page.locator('button:has-text("Renew"), .btn:has-text("Renew")').first
            if renew_btn.is_visible():
                renew_btn.click()
                time.sleep(3)
                return True
            return False

        # ── 步骤 4：处理 2 号图点击白色三角形 ────────────────────────
        def step_click_white_play():
            print("=" * 50)
            print("步骤 3：点击 2 号图白色三角形播放按钮")
            handle_ad_popup()
            # 2 号图的白色三角形通常是一个 svg 或大按钮
            play_btn = page.locator('div[role="dialog"] svg, .modal-body svg').first
            if play_btn.is_visible():
                play_btn.click()
                print("✅ 2 号图播放已点击")
                time.sleep(3)
                return True
            return False

        # ── 步骤 5：处理 3 号图点击 YouTube 红色按钮 ──────────────────
        def step_click_youtube_red():
            print("=" * 50)
            print("步骤 4：点击 3 号图红色 YouTube 按钮")
            handle_ad_popup()
            time.sleep(2)
            # YouTube 按钮通常在 iframe 里面
            clicked = False
            for frame in page.frames:
                if "youtube.com" in frame.url:
                    red_btn = frame.locator(".ytp-large-play-button")
                    if red_btn.is_visible():
                        red_btn.click()
                        clicked = True
                        break
            
            if not clicked:
                # 尝试直接在页面点
                page.mouse.click(640, 360) # 点击播放器中心
            
            print("✅ 视频开始播放，进入等待期...")
            return True

        # ── 步骤 6：处理 4 号图点击 Get+12Hours ─────────────────────
        def step_wait_for_reward():
            print("=" * 50)
            print("步骤 5：等待 4 号图奖励窗口出现（约 240-300秒）")
            start_time = time.time()
            while time.time() - start_time < 400: # 最多等 400 秒
                handle_ad_popup()
                body = get_body_text()
                
                # 检测 4 号图的关键文字
                if "Get +12 Hours" in body:
                    print("🎉 发现 4 号图！点击 Get +12 Hours")
                    reward_btn = page.locator('button:has-text("Get +12 Hours")').first
                    if reward_btn.is_visible():
                        reward_btn.click()
                        time.sleep(2)
                        print("✨ 整个流程完成！")
                        return True
                
                if int(time.time() - start_time) % 30 == 0:
                    print(f"仍在播放中... 已等待 {int(time.time() - start_time)} 秒")
                
                time.sleep(10)
            return False

        # ── 启动主循环 ────────────────────────────────────────────────
        try:
            step_prepare()
            if step_click_renew():
                if step_click_white_play():
                    if step_click_youtube_red():
                        step_wait_for_reward()
        except Exception as e:
            print(f"❌ 运行中出错: {e}")
            page.screenshot(path="error_debug.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
