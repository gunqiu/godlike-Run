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
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        def save_debug(name):
            try:
                page.screenshot(path=name, full_page=True)
                print(f"[截图已保存] {name}")
            except Exception as e:
                print(f"[截图失败] {name}: {e}")

        def fail(step_name):
            save_debug(f"FAIL_{step_name}.png")
            print(f"❌ 任务失败于步骤：{step_name}")

        def safe_goto(url, name):
            print(f"打开 {name}...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(5)
                return True
            except:
                time.sleep(5)
                return True

        def get_body_text():
            try:
                return page.locator("body").inner_text(timeout=1500)
            except:
                return ""

        # ── 自动清理干扰弹窗（推广、客服、聊天窗） ────────────────

        def cleanup_overlays():
            """清理所有可能遮挡点击的元素"""
            try:
                # 1. 处理图片中的推广弹窗
                body_text = get_body_text()
                if "Do you love Godlike?" in body_text:
                    page.keyboard.press("Escape")
                    # 尝试点击那个特定的 X
                    x_btn = page.locator('div[role="dialog"] button:has(svg), button:has-text("✕")').first
                    if x_btn.is_visible(): x_btn.click()
                
                # 2. 处理右下角的客服聊天窗 (Godlike Panel)
                # 这种窗口通常在 iframe 里或者有特定的关闭类名
                chat_close = page.locator('button[aria-label="Close"], .crisp-client [data-chat-close="true"], button:has-text("Continue conversation") + button').first
                if chat_close.is_visible():
                    chat_close.click()
                    print("🧹 已清理客服聊天窗")

            except:
                pass

        # ── 步骤 1：登录 ──────────────────────────────────────────────

        def step_login():
            print("=" * 50)
            print("步骤 1：登录")
            safe_goto(LOGIN_URL, "登录页")
            try:
                sw = page.get_by_text("Through Login/Password")
                if sw.is_visible(timeout=3000): sw.click(force=True)
            except: pass
            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=25000)
            print("✅ 登录成功")

        # ── 步骤 2：打开服务器页面 ────────────────────────────────────

        def step_open_server():
            print("=" * 50)
            print("步骤 2：打开服务器页面")
            safe_goto(SERVER_URL, "服务器管理页")
            time.sleep(3)
            print("✅ 服务器页面已打开")

        # ── 步骤 3：点击 Renew ────────────────────────────────────────

        def step_click_renew(max_seconds=40):
            print("=" * 50)
            print("步骤 3：点击 Renew 按钮")
            start = time.time()
            while time.time() - start < max_seconds:
                cleanup_overlays()
                result = page.evaluate("""
                    () => {
                        function vis(el){
                            const r=el.getBoundingClientRect();
                            return r.width>0 && r.height>0;
                        }
                        const btns = Array.from(document.querySelectorAll('button, div, span'));
                        const renewBtn = btns.find(el => el.innerText.includes('Renew') && vis(el));
                        if(renewBtn) { renewBtn.click(); return true; }
                        return false;
                    }
                """)
                if result:
                    time.sleep(3)
                    print("✅ Renew 已点击")
                    return True
                time.sleep(1)
            fail("click_renew")
            return False

        # ── 步骤 4：等待 Choose Renewal Method ───────────────────────

        def step_wait_renewal_popup(max_seconds=25):
            print("=" * 50)
            print("步骤 4：等待 Choose Renewal Method 弹窗")
            start = time.time()
            while time.time() - start < max_seconds:
                cleanup_overlays()
                if "Choose Renewal Method" in get_body_text():
                    print("✅ Choose Renewal Method 弹窗已出现")
                    return True
                time.sleep(1)
            fail("renewal_popup")
            return False

        # ── 步骤 5：点击播放图标 ──────────────────────────────────────

        def step_click_play_option():
            print("=" * 50)
            print("步骤 5：点击中央播放图标 ▶")
            
            # 先强制清理一次干扰，防止客服窗口挡住播放按钮
            cleanup_overlays()
            time.sleep(1)

            # 改进后的点击逻辑：优先点击弹窗中心的 svg 图标（即播放按钮）
            clicked = page.evaluate("""
                () => {
                    function vis(el){
                        const r=el.getBoundingClientRect();
                        return r.width>0 && r.height>0;
                    }
                    // 找到包含 'watching video' 的弹窗
                    const dialog = document.querySelector('div[role="dialog"], .modal');
                    if (!dialog) return {ok: false, msg: 'no dialog'};
                    
                    // 在弹窗内寻找那个白色的播放图标（通常是 svg 或带有特定路径的元素）
                    const playBtn = dialog.querySelector('svg, .play-icon, i.fa-play');
                    if (playBtn && vis(playBtn)) {
                        playBtn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                        return {ok: true, method: 'svg-icon'};
                    }
                    
                    // 兜底：点击包含该文字的整个容器的中心
                    const textEl = Array.from(dialog.querySelectorAll('*')).find(el => el.innerText.includes('Get +24 hours'));
                    if (textEl && vis(textEl)) {
                        textEl.click();
                        return {ok: true, method: 'text-container'};
                    }
                    return {ok: false};
                }
            """)
            print(f"点击尝试结果：{clicked}")
            time.sleep(3)

            # 验证是否跳转（如果弹窗消失了或文字变了，说明点中了）
            if "Choose Renewal Method" not in get_body_text():
                print("✅ 已成功进入视频播放流程")
                return True

            # 终极兜底：根据你的 FAIL 图片，强制点击屏幕中心位置
            print("⚠️ 自动点击未响应，尝试强制坐标点击中心...")
            page.mouse.click(640, 400) # 1280*800 的中心附近
            time.sleep(2)
            
            if "Choose Renewal Method" not in get_body_text():
                return True

            fail("click_play_option")
            return False

        # ── 步骤 6 & 7：播放与领取（逻辑保持） ────────────────────────

        def step_click_youtube_play():
            print("=" * 50)
            print("步骤 6：点击 YouTube 播放")
            time.sleep(5)
            try:
                for frame in page.frames:
                    if "youtube" in frame.url:
                        btn = frame.locator(".ytp-large-play-button").first
                        if btn.is_visible():
                            btn.click()
                            print("✅ 视频已开始播放")
                            return True
            except: pass
            return True

        def step_wait_and_claim_reward(total_wait=300):
            print("=" * 50)
            print(f"步骤 7：等待奖励领取按钮...")
            start = time.time()
            while time.time() - start < total_wait:
                cleanup_overlays() # 过程中也可能弹出广告，点掉它
                body = get_body_text()
                if "Get +24 hours" in body and "watching" not in body:
                    page.get_by_text("Get +24 hours").first.click()
                    print("🎉 续期成功！")
                    return True
                time.sleep(5)
            return False

        # ── 主流程 ────────────────────────────────────────────────────
        try:
            step_login()
            step_open_server()
            if step_click_renew() and step_wait_renewal_popup():
                if step_click_play_option():
                    step_click_youtube_play()
                    step_wait_and_claim_reward()
        finally:
            browser.close()

if __name__ == "__main__":
    run()
