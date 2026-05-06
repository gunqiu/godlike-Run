import os
import time
from playwright.sync_api import sync_playwright

# 配置信息
LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 固定窗口大小，确保坐标点击准确
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def save_debug(name):
            page.screenshot(path=f"FINAL_DEBUG_{name}.png")
            print(f"📸 调试截图已保存: FINAL_DEBUG_{name}.png")

        # --- 步骤 1: 登录 ---
        print("\n" + "="*40)
        print("步骤 1: 执行登录")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        time.sleep(3)
        try:
            # 兼容切换登录方式
            if page.get_by_text("Through Login/Password").is_visible():
                page.get_by_text("Through Login/Password").click(force=True)
        except: pass
        
        page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
        page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
        page.locator('button:has-text("Login")').first.click()
        page.wait_for_url(lambda url: "login" not in url, timeout=30000)
        print("✅ 登录成功")

        # --- 步骤 2: 点击 1 号图 Renew ---
        print("\n" + "="*40)
        print("步骤 2: 前往服务器页面并点击 Renew")
        page.goto(SERVER_URL, wait_until="domcontentloaded")
        time.sleep(12) # 多等一会，确保页面完全刷出来

        # 尝试坐标点击：根据截图，Renew 按钮大约在左侧 240, 480 的位置
        # 我们先尝试用最准的“坐标+穿透”组合拳
        print("🎯 正在执行坐标穿透点击 (针对 1 号图 Renew)...")
        page.mouse.click(240, 485) 
        time.sleep(5)

        # --- 步骤 3: 点击 2 号图 (白色三角形) ---
        print("\n" + "="*40)
        print("步骤 3: 处理 2 号图弹窗")
        # 2 号图弹窗通常在屏幕正中央
        page.mouse.click(640, 400) 
        print("✅ 已尝试点击屏幕中心播放图标")
        time.sleep(5)

        # --- 步骤 4: 点击 3 号图 (YouTube 红色按钮) ---
        print("\n" + "="*40)
        print("步骤 4: 激活 YouTube 播放")
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
            page.mouse.click(640, 360) # 兜底点击视频中心
            print("⚠️ 未找到红色按钮，已执行坐标兜底点击")

        # --- 步骤 5: 等待 4 号图 ---
        print("\n" + "="*40)
        print("步骤 5: 等待领取奖励 (约 5-8 分钟)")
        start_time = time.time()
        while time.time() - start_time < 500:
            content = page.content()
            if "Get +12 Hours" in content:
                print(f"🎉 成功发现 4 号图奖励按钮！耗时: {int(time.time()-start_time)}秒")
                # 奖励按钮通常很大，直接用文字点击
                page.get_by_text("Get +12 Hours").first.click(force=True)
                print("✨ 续期任务全部完成！")
                time.sleep(5)
                browser.close()
                return

            if int(time.time() - start_time) % 60 == 0:
                print(f"计时中: 已等待 {int(time.time() - start_time)} 秒...")
                # 顺手按个 ESC 键，防止 5 号图弹窗干扰
                page.keyboard.press("Escape")
            
            time.sleep(10)

        print("❌ 最终超时，未看到奖励按钮")
        save_debug("timeout_reward")
        browser.close()

if __name__ == "__main__":
    run()
