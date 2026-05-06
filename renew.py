import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# 配置信息
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

        # 优化：拦截图片和无用脚本，加快加载速度
        def block_aggressively(route):
            if route.request.resource_type in ["image", "media", "font"] or "hubspot" in route.request.url:
                route.abort()
            else:
                route.continue_()
        page.route("**/*", block_aggressively)

        def clear_battlefield():
            """暴力删除所有干扰元素"""
            try:
                page.evaluate("""
                    () => {
                        const badSelectors = [
                            'div[class*="modal"]', 'div[class*="dialog"]', 'iframe', 
                            '.fixed.bottom-4', 'div[id*="hubspot"]', '.banner',
                            'div:contains("How likely")', 'div:contains("We are online")'
                        ];
                        badSelectors.forEach(s => {
                            document.querySelectorAll(s).forEach(el => el.remove());
                        });
                        document.body.style.overflow = 'auto';
                    }
                """)
            except: pass

        # --- 步骤 1: 登录 ---
        print("\n" + "="*40 + "\n步骤 1: 执行登录")
        try:
            page.goto(LOGIN_URL, wait_until="commit", timeout=60000)
            # 增加对邮箱框的重试逻辑
            email_input = page.locator('input[type="email"]').first
            email_input.wait_for(state="visible", timeout=45000)
            
            email_input.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            
            page.wait_for_url(lambda url: "login" not in url, timeout=30000)
            print("✅ 登录成功")
        except Exception as e:
            print(f"❌ 登录环节超时或失败: {e}")
            page.screenshot(path="LOGIN_ERROR.png")
            browser.close()
            return

        # --- 步骤 2: 进入服务器页面并点击 Renew ---
        print("\n" + "="*40 + "\n步骤 2: 清理弹窗并点击 Renew")
        page.goto(SERVER_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)
        
        clear_battlefield()
        page.keyboard.press("Escape")
        
        # 针对 1 号图 Renew 按钮
        renew_btn = page.locator('button:has-text("Renew"), a:has-text("Renew"), [role="button"]:has-text("Renew")').first
        if renew_btn.is_visible():
            print("🎯 发现 Renew 按钮，执行点击...")
            renew_btn.click(force=True)
        else:
            print("⚠️ 未发现按钮标签，执行坐标保底点击...")
            page.mouse.click(240, 485)
        time.sleep(8)

        # --- 步骤 3: 处理 2 号图 (白色三角形) ---
        print("\n" + "="*40 + "\n步骤 3: 点击 2 号图播放图标")
        clear_battlefield()
        play_svg = page.locator('div[role="dialog"] svg, .modal-body svg').first
        if play_svg.is_visible():
            play_svg.click(force=True)
            print("✅ 已点击播放图标")
        else:
            page.mouse.click(640, 400)
            print("⚠️ 尝试坐标点击屏幕中心")
        time.sleep(5)

        # --- 步骤 4: 点击 3 号图 (YouTube 红色按钮) ---
        print("\n" + "="*40 + "\n步骤 4: 激活视频播放")
        # 因为拦截了脚本，视频可能需要手动点击中心
        page.mouse.click(640, 360)
        print("✅ 已执行坐标点击视频中心")

        # --- 步骤 5: 等待 4 号图 ---
        print("\n" + "="*40 + "\n步骤 5: 等待领取奖励 (约 8 分钟)")
        start_time = time.time()
        while time.time() - start_time < 540: # 增加到 9 分钟
            if int(time.time() - start_time) % 60 == 0:
                clear_battlefield()
                page.keyboard.press("Escape")
                print(f"计时中: 已等待 {int(time.time() - start_time)} 秒...")

            # 检查是否有 Get +12 Hours 按钮
            content = page.content()
            if "Get +12 Hours" in content:
                print(f"🎉 发现奖励按钮！")
                reward_btn = page.get_by_text("Get +12 Hours").first
                if reward_btn.is_visible():
                    reward_btn.click(force=True)
                    print("✨ 续期任务全部完成！")
                    time.sleep(5)
                    browser.close()
                    return
            time.sleep(10)

        print("❌ 最终超时，未看到奖励按钮")
        page.screenshot(path="FINAL_TIMEOUT.png")
        browser.close()

if __name__ == "__main__":
    run()
