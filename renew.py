import os
import time
from playwright.sync_api import sync_playwright

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

        def clear_popups():
            """强行删除页面上所有的干扰弹窗和遮盖物"""
            try:
                page.evaluate("""
                    () => {
                        // 定义需要删除的干扰元素特征（针对截图中的评分窗、客服窗、顶部横幅）
                        const selectors = [
                            'div[class*="modal"]', 
                            'div[class*="dialog"]',
                            'iframe[title*="chat"]',
                            'div[id*="hubspot"]',
                            'div[class*="banner"]',
                            '.fixed.bottom-4', // 评分弹窗常见的类名
                            'div:has(> h2:contains("How likely"))'
                        ];
                        selectors.forEach(s => {
                            document.querySelectorAll(s).forEach(el => el.remove());
                        });
                        // 强制去掉 body 的滚动锁定
                        document.body.style.overflow = 'auto';
                    }
                """)
            except: pass

        # --- 步骤 1: 登录 ---
        print("\n" + "="*40 + "\n步骤 1: 执行登录")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        time.sleep(3)
        page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
        page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
        page.locator('button:has-text("Login")').first.click()
        page.wait_for_url(lambda url: "login" not in url, timeout=30000)
        print("✅ 登录成功")

        # --- 步骤 2: 点击 1 号图 Renew ---
        print("\n" + "="*40 + "\n步骤 2: 清理弹窗并点击 Renew")
        page.goto(SERVER_URL, wait_until="domcontentloaded")
        time.sleep(15) # 多等会儿，让那些烦人的弹窗蹦出来
        
        # 核心：先清理页面，再点击
        clear_popups()
        page.keyboard.press("Escape") 
        
        # 使用更稳健的定位方式：找到包含 "Renew" 文本的紫色按钮并滚动到它
        renew_btn = page.locator('button:has-text("Renew"), a:has-text("Renew")').first
        if renew_btn.is_visible():
            print("🎯 发现 Renew 按钮，执行滚动点击...")
            renew_btn.scroll_into_view_if_needed()
            renew_btn.click(force=True)
        else:
            print("⚠️ 未发现按钮标签，尝试坐标保底点击...")
            page.mouse.click(240, 485) # 你的 Renew 按钮大致坐标
            
        time.sleep(8)

        # --- 步骤 3: 处理 2 号图 (白色三角形) ---
        print("\n" + "="*40 + "\n步骤 3: 点击 2 号图播放图标")
        clear_popups() # 再次清理，防止新弹窗
        # 寻找弹窗中的 svg 播放图标
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
        found_yt = False
        for frame in page.frames:
            if "youtube" in frame.url:
                try:
                    frame.locator(".ytp-large-play-button").click(force=True, timeout=5000)
                    found_yt = True
                    print("✅ 已点击 YouTube 红色按钮")
                    break
                except: continue
        if not found_yt:
            page.mouse.click(640, 360)
            print("⚠️ 已执行坐标兜底点击视频中心")

        # --- 步骤 5: 等待 4 号图 ---
        print("\n" + "="*40 + "\n步骤 5: 等待领取奖励 (约 8 分钟)")
        start_time = time.time()
        while time.time() - start_time < 500:
            # 持续清理可能蹦出来的干扰
            if int(time.time() - start_time) % 60 == 0:
                clear_popups()
                page.keyboard.press("Escape")
                print(f"计时中: 已等待 {int(time.time() - start_time)} 秒...")

            content = page.content()
            if "Get +12 Hours" in content:
                print(f"🎉 发现奖励按钮！")
                page.get_by_text("Get +12 Hours").first.click(force=True)
                print("✨ 续期任务全部完成！")
                time.sleep(5)
                browser.close()
                return
            
            time.sleep(10)

        page.screenshot(path="FINAL_ERROR.png")
        print("❌ 最终超时，截图已保存为 FINAL_ERROR.png")
        browser.close()

if __name__ == "__main__":
    run()
