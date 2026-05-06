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
            try:
                page.screenshot(path=f"FAIL_{name}.png", full_page=True)
                print(f"[截图已保存] FAIL_{name}.png")
            except Exception as e:
                print(f"[截图失败] {name}: {e}")

        def get_body_text():
            try:
                return page.locator("body").inner_text(timeout=2000)
            except:
                return ""

        # ── 针对 5 号图：推广弹窗处理 ──────────────────────────
        def close_5_popup():
            """只要发现 5 号图，立即点击右上角 X 关掉"""
            try:
                # 只有当发现 5 号图特有的文字时才操作
                body = get_body_text()
                if "Do you love Godlike?" in body or "Claim -50% Off" in body:
                    print("⚠️ 发现 5 号图推广弹窗，正在清理...")
                    # 尝试点击右上角的 X 按钮
                    x_btn = page.locator('div[role="dialog"] button:has(svg), .modal-header button').first
                    if x_btn.is_visible(timeout=1000):
                        x_btn.click()
                        time.sleep(1)
                    else:
                        page.keyboard.press("Escape")
                    return True
            except:
                pass
            return False

        # ── 步骤 1：登录（恢复你最稳的原始逻辑） ──────────────────────
        def step_login():
            print("=" * 50)
            print("步骤 1：登录")
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            try:
                sw = page.get_by_text("Through Login/Password")
                if sw.is_visible(timeout=3000):
                    sw.click(force=True)
            except:
                pass
            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=25000)
            print("✅ 登录成功")

        # ── 步骤 2：进入 1 号图页面并点击 Renew ───────────────────
        def step_click_renew():
            print("=" * 50)
            print("步骤 2：点击 1 号图 Renew 按钮")
            page.goto(SERVER_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            
            start = time.time()
            while time.time() - start < 30:
                close_5_popup() # 随时清理 5 号图
                # 定位 1 号图的 Renew 按钮
                btn = page.locator('button:has-text("Renew"), [role="button"]:has-text("Renew")').first
                if btn.is_visible():
                    btn.click()
                    print("✅ 1 号图 Renew 已点击")
                    time.sleep(3)
                    return True
                time.sleep(1)
            save_debug("step2_renew_fail")
            return False

        # ── 步骤 3：处理 2 号图（点击白色三角形） ─────────────────────
        def step_click_2_play():
            print("=" * 50)
            print("步骤 3：点击 2 号图播放图标")
            start = time.time()
            while time.time() - start < 20:
                close_5_popup() # 随时清理 5 号图
                # 寻找 2 号图弹窗中心的播放 svg
                play_svg = page.locator('div[role="dialog"] svg, .modal-body svg').first
                if play_svg.is_visible():
                    play_svg.click()
                    print("✅ 2 号图播放图标已点击")
                    time.sleep(3)
                    return True
                time.sleep(1)
            save_debug("step3_play_fail")
            return False

        # ── 步骤 4：处理 3 号图（YouTube 红色按钮） ──────────────────
        def step_click_3_youtube():
            print("=" * 50)
            print("步骤 4：点击 3 号图红色 YouTube 按钮")
            time.sleep(5)
            close_5_popup()
            
            # 在 iframe 中找红色按钮
            found = False
            for frame in page.frames:
                if "youtube" in frame.url:
                    try:
                        red_btn = frame.locator(".ytp-large-play-button")
                        if red_btn.is_visible(timeout=3000):
                            red_btn.click()
                            found = True
                            print("✅ 3 号图 YouTube 按钮已点击")
                            break
                    except:
                        continue
            
            if not found:
                print("⚠️ 未发现红色按钮，尝试点击坐标中心兜底")
                page.mouse.click(640, 360)
            return True

        # ── 步骤 5：处理 4 号图（领取奖励） ──────────────────────────
        def step_wait_4_reward():
            print("=" * 50)
            print("步骤 5：等待 4 号图奖励出现 (240s+)")
            start = time.time()
            while time.time() - start < 450:
                close_5_popup() # 过程中可能蹦出 5 号图干扰
                
                body = get_body_text()
                # 检测 4 号图关键文本
                if "Get +12 Hours" in body:
                    print("🎉 发现 4 号图！准备领取")
                    btn = page.get_by_text("Get +12 Hours").first
                    if btn.is_visible():
                        btn.click()
                        time.sleep(2)
                        print("✨ 流程圆满完成！服务器已续期")
                        return True
                
                if int(time.time() - start) % 60 == 0:
                    print(f"已经在播放中等待了 {int(time.time() - start)} 秒...")
                time.sleep(5)
            
            save_debug("step5_reward_timeout")
            return False

        # ── 主流程执行 ──────────────────────────────────────────────
        try:
            step_login()
            if step_click_renew():
                if step_click_2_play():
                    if step_click_3_youtube():
                        step_wait_4_reward()
        except Exception as e:
            print(f"❌ 运行异常: {e}")
            save_debug("crash")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
