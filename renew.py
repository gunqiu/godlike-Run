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

        def save_debug(name):
            page.screenshot(path=f"debug_{name}.png", full_page=True)
            print(f"📸 [截图已保存] debug_{name}.png")

        def get_body_text():
            try: return page.locator("body").inner_text(timeout=1000)
            except: return ""

        # ── 逻辑 5：处理 5 号图中的特殊窗口（推广弹窗） ────────────────
        def handle_ad_popup():
            """发现 5 号图窗口就点击右上角叉去掉"""
            try:
                if "Do you love Godlike?" in get_body_text():
                    print("⚠️ 检测到 5 号图推广弹窗，正在清理...")
                    # 尝试点击右上角的 X
                    close_btn = page.locator('div[role="dialog"] button:has(svg), .modal-header button').first
                    if close_btn.is_visible(timeout=2000):
                        close_btn.click()
                    else:
                        page.keyboard.press("Escape")
                    time.sleep(1.5)
            except: pass

        # ── 步骤 1：登录 ──────────────────────────────────────────────
        def step_login():
            print("\n" + "="*30 + " 步骤 1: 登录 " + "="*30)
            page.goto(LOGIN_URL, wait_until="networkidle")
            try:
                page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
                page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
                page.locator('button:has-text("Login")').first.click()
                page.wait_for_url(lambda url: "login" not in url, timeout=20000)
                print("✅ 登录成功")
            except Exception as e:
                print(f"❌ 登录失败: {e}")
                save_debug("login_fail")

        # ── 步骤 2：进入 1 号图页面并点击 Renew ────────────────────────
        def step_click_renew():
            print("\n" + "="*30 + " 步骤 2: 点击 1 号图 Renew " + "="*30)
            page.goto(SERVER_URL, wait_until="domcontentloaded")
            time.sleep(5)
            handle_ad_popup()
            
            # 使用更强大的脚本定位 Renew 按钮
            clicked = page.evaluate("""
                () => {
                    const btns = Array.from(document.querySelectorAll('button, div, span, a'));
                    const target = btns.find(el => el.innerText === 'Renew' && el.getBoundingClientRect().width > 0);
                    if (target) {
                        target.scrollIntoView();
                        target.click();
                        return true;
                    }
                    return false;
                }
            """)
            if clicked:
                print("✅ 1 号图 Renew 按钮已点击")
                return True
            else:
                print("❌ 未找到 Renew 按钮")
                save_debug("no_renew_btn")
                return False

        # ── 步骤 3：处理 2 号图点击白色三角形 ────────────────────────
        def step_click_white_play():
            print("\n" + "="*30 + " 步骤 3: 点击 2 号图播放图标 " + "="*30)
            # 等待 2 号图弹窗出现
            start = time.time()
            while time.time() - start < 15:
                handle_ad_popup()
                # 寻找包含播放图标的 dialog
                play_icon = page.locator('div[role="dialog"] svg, .modal-body svg').first
                if play_icon.is_visible():
                    play_icon.click()
                    print("✅ 2 号图白色播放图标已点击")
                    return True
                time.sleep(1)
            print("❌ 未找到 2 号图播放图标")
            save_debug("no_white_play")
            return False

        # ── 步骤 4：处理 3 号图 YouTube 按钮 ─────────────────────────
        def step_click_youtube_red():
            print("\n" + "="*30 + " 步骤 4: 点击 3 号图 YouTube 红色按钮 " + "="*30)
            time.sleep(5)
            handle_ad_popup()
            
            # 尝试在所有 frame 中寻找红色按钮
            found = False
            for frame in page.frames:
                try:
                    red_btn = frame.locator(".ytp-large-play-button")
                    if red_btn.is_visible(timeout=3000):
                        red_btn.click()
                        found = True
                        print("✅ 已在 iframe 中点中 YouTube 按钮")
                        break
                except: continue
            
            if not found:
                print("⚠️ 未点中红色按钮，尝试点击屏幕中心坐标...")
                page.mouse.click(640, 380)
            
            return True

        # ── 步骤 5：处理 4 号图领取奖励 ──────────────────────────────
        def step_wait_for_reward():
            print("\n" + "="*30 + " 步骤 5: 等待 4 号图奖励按钮 " + "="*30)
            start_time = time.time()
            while time.time() - start_time < 480: # 增加到 480 秒保险
                handle_ad_popup()
                body = get_body_text()
                
                # 寻找 4 号图的奖励按钮
                if "Get +12 Hours" in body:
                    print(f"🎉 发现奖励按钮！耗时: {int(time.time()-start_time)}秒")
                    reward_btn = page.get_by_text("Get +12 Hours").first
                    if reward_btn.is_visible():
                        reward_btn.click()
                        print("✨ 奖励领取成功！流程结束。")
                        return True
                
                if int(time.time() - start_time) % 30 == 0:
                    print(f"正在看片中... 已过 {int(time.time() - start_time)} 秒")
                
                time.sleep(5)
            
            print("❌ 超过 8 分钟未见奖励按钮")
            save_debug("reward_timeout")
            return False

        # ── 执行流程 ──────────────────────────────────────────────────
        try:
            step_login()
            if step_click_renew():
                if step_click_white_play():
                    if step_click_youtube_red():
                        step_wait_for_reward()
        except Exception as e:
            print(f"🔥 程序崩溃: {e}")
            save_debug("crash")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
