import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# 配置信息
LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"

def run():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 辅助函数：保存调试截图
        def save_debug(name):
            try:
                page.screenshot(path=f"DEBUG_{name}.png", full_page=True)
                print(f"📸 [调试截图已保存] DEBUG_{name}.png")
            except:
                pass

        # 辅助函数：获取当前页面文本
        def get_body_text():
            try:
                return page.locator("body").inner_text(timeout=2000)
            except:
                return ""

        # ── 步骤 1：登录 ──────────────────────────────────────────────
        def step_login():
            print("\n" + "="*50)
            print("步骤 1：正在登录...")
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            # 处理可能的登录方式切换
            try:
                sw = page.get_by_text("Through Login/Password")
                if sw.is_visible(timeout=3000):
                    sw.click(force=True)
            except:
                pass

            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            
            # 等待登录成功跳转
            page.wait_for_url(lambda url: "login" not in url, timeout=30000)
            print("✅ 登录成功")

        # ── 步骤 2：进入服务器页面并点击 Renew (解决 1 号图/5 号图冲突) ───
        def step_click_renew():
            print("\n" + "="*50)
            print("步骤 2：寻找 Renew 按钮 (处理 1 号图)...")
            page.goto(SERVER_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(10) # 额外多等一会儿，让控制台加载完

            start_time = time.time()
            while time.time() - start_time < 45:
                # 尝试多种方式定位那个蓝色的 Renew 按钮
                renew_btn = page.locator('button:has-text("Renew"), [role="button"]:has-text("Renew")').first
                
                if renew_btn.is_visible():
                    print("🎯 捕捉到 Renew 按钮！正在穿透干扰进行点击...")
                    # force=True 非常关键：即使被 5 号图挡住也能点中
                    renew_btn.click(force=True)
                    print("✅ 1 号图 Renew 按钮点击成功")
                    time.sleep(5)
                    return True
                
                # 如果没找到按钮，可能是被广告弹窗完全覆盖了，尝试按一次 ESC
                page.keyboard.press("Escape")
                time.sleep(2)
            
            print("❌ 无法定位到 Renew 按钮")
            save_debug("no_renew_found")
            return False

        # ── 步骤 3：点击白色三角形 (处理 2 号图) ──────────────────────
        def step_click_2_play():
            print("\n" + "="*50)
            print("步骤 3：点击播放图标 (处理 2 号图)...")
            start = time.time()
            while time.time() - start < 20:
                # 定位弹窗中的播放 SVG 图标
                play_icon = page.locator('div[role="dialog"] svg, .modal-body svg').first
                if play_icon.is_visible():
                    play_icon.click(force=True)
                    print("✅ 2 号图播放图标已点击")
                    time.sleep(3)
                    return True
                time.sleep(1)
            
            print("❌ 未发现 2 号图播放图标")
            save_debug("no_2_play_icon")
            return False

        # ── 步骤 4：点击 YouTube 红色按钮 (处理 3 号图) ────────────────
        def step_click_3_youtube():
            print("\n" + "="*50)
            print("步骤 4：激活视频播放 (处理 3 号图)...")
            time.sleep(5)
            
            found = False
            for frame in page.frames:
                if "youtube" in frame.url:
                    try:
                        red_btn = frame.locator(".ytp-large-play-button")
                        if red_btn.is_visible(timeout=3000):
                            red_btn.click(force=True)
                            found = True
                            print("✅ 3 号图 YouTube 按钮已点击")
                            break
                    except:
                        continue
            
            if not found:
                print("⚠️ 未点中红色按钮，尝试点击画面中心")
                page.mouse.click(640, 360)
            return True

        # ── 步骤 5：等待并领取奖励 (处理 4 号图) ──────────────────────
        def step_wait_4_reward():
            print("\n" + "="*50)
            print("步骤 5：等待奖励按钮出现 (处理 4 号图)...")
            start_time = time.time()
            # 视频通常需要 4 分钟以上
            while time.time() - start_time < 480:
                body_text = get_body_text()
                
                if "Get +12 Hours" in body_text:
                    print(f"🎉 看到奖励了！耗时: {int(time.time() - start_time)} 秒")
                    reward_btn = page.get_by_text("Get +12 Hours").first
                    if reward_btn.is_visible():
                        reward_btn.click(force=True)
                        print("✨ 任务圆满完成！")
                        time.sleep(5)
                        return True
                
                if int(time.time() - start_time) % 60 == 0:
                    print(f"已经在看视频中了... 已过 {int(time.time() - start_time)} 秒")
                
                # 期间如果蹦出 5 号图弹窗，顺手按 ESC 关掉
                if "Do you love Godlike?" in body_text:
                    page.keyboard.press("Escape")
                
                time.sleep(5)
            
            print("❌ 等待超时，未看到 4 号图奖励按钮")
            save_debug("reward_timeout")
            return False

        # ── 执行整个工作流 ────────────────────────────────────────────
        try:
            step_login()
            if step_click_renew():
                if step_click_2_play():
                    if step_click_3_youtube():
                        step_wait_4_reward()
        except Exception as e:
            print(f"🔥 程序运行崩溃: {e}")
            save_debug("crash_report")
        finally:
            browser.close()
            print("\n" + "="*50)
            print("脚本运行结束")

if __name__ == "__main__":
    run()
