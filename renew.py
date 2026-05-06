import os
import time
import threading
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

        _watcher_stop = threading.Event()

        def _premium_watcher():
            while not _watcher_stop.is_set():
                try:
                    body = page.locator("body").inner_text(timeout=1000)
                    if "Do you love Godlike?" in body or "Claim -50% Off" in body:
                        page.evaluate("""
                            () => {
                                function textOf(el){return(el.innerText||el.textContent||'').trim();}
                                function vis(el){
                                    const r=el.getBoundingClientRect(),s=window.getComputedStyle(el);
                                    return r.width>0&&r.height>0&&s.display!=='none';
                                }
                                for(const el of document.querySelectorAll('button,a,span')){
                                    if(textOf(el).includes("I'm fine with waiting")&&vis(el)){
                                        el.click(); return;
                                    }
                                }
                            }
                        """)
                except: pass
                time.sleep(2)

        def start_watcher():
            t = threading.Thread(target=_premium_watcher, daemon=True)
            t.start()
            return t

        def save_debug(name):
            try:
                page.screenshot(path=f"step_{name}.png", full_page=True)
                print(f"[截图保存] step_{name}.png")
            except: pass

        def get_body_text():
            try: return page.locator("body").inner_text(timeout=1500)
            except: return ""

        # ── 步骤 1：登录 ──────────────────────────────────────────────
        print("=" * 50)
        print("步骤 1：登录流程")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        save_debug("1_1_login_page")
        page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
        page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
        page.locator('button:has-text("Login")').first.click()
        page.wait_for_url(lambda url: "login" not in url, timeout=25000)
        save_debug("1_3_login_success")

        # ── 步骤 2：打开服务器页面 ─────────────────────────────────────
        print("=" * 50)
        print("步骤 2：打开服务器管理页面")
        page.goto(SERVER_URL, wait_until="domcontentloaded")
        time.sleep(5)
        save_debug("2_1_server_page_loaded")

        # ── 第二步到第三步之间：等待并开启监控 ────────────────────────
        print(">>> 等待 3 秒并启动弹窗监控...")
        time.sleep(3)
        start_watcher()
        save_debug("2_5_watcher_started")

        # ── 步骤 3：点击 Renew 按钮 ──────────────────────────────────
        print("=" * 50)
        print("步骤 3：点击 Renew 按钮")
        save_debug("3_1_before_renew")
        page.evaluate("""
            () => {
                const els = document.querySelectorAll('button, [role="button"]');
                for(const el of els){
                    if(el.innerText.includes('Renew')){ el.click(); return; }
                }
            }
        """)
        time.sleep(3)
        save_debug("3_2_after_renew")

        # ── 步骤 4：处理续费方式选择（点击三角形图标） ────────────────
        print("=" * 50)
        print("步骤 4：处理续费弹窗并点击三角形")
        
        # 4.1 等待弹窗出现
        popup_detected = False
        for _ in range(20):
            if "Choose Renewal Method" in get_body_text():
                popup_detected = True
                print("✅ 续费弹窗已出现")
                save_debug("4_1_renewal_method_popup")
                break
            time.sleep(1)

        if popup_detected:
            # 4.2 执行点击三角形逻辑
            print(">>> 正在尝试点击三角形播放图标...")
            clicked = page.evaluate("""
                () => {
                    function vis(el){
                        const r=el.getBoundingClientRect();
                        return r.width > 0 && r.height > 0;
                    }
                    // 优先寻找 SVG 里的三角形标签 polygon
                    const triangle = document.querySelector('polygon, [class*="play"], svg');
                    if(triangle && vis(triangle)){
                        triangle.scrollIntoView({block:'center'});
                        triangle.click();
                        return {ok: true, method: 'dom_triangle'};
                    }
                    return {ok: false};
                }
            """)
            print(f"DOM点击尝试结果: {clicked}")
            time.sleep(2)

            # 4.3 坐标兜底 (针对截图 step_4_1_renewal_method_popup.jpg 中的中心位置)
            if "Choose Renewal Method" in get_body_text():
                print(">>> DOM可能未触发，执行中心坐标点击...")
                # 在 1280x800 下，弹窗中心播放图标约在 (640, 260)
                page.mouse.click(640, 260)
                time.sleep(2)
            
            save_debug("4_2_after_clicking_triangle")

        # ── 步骤 5-7：后续流程 ──────────────────────────────────────
        print("=" * 50)
        print("后续步骤：等待视频播放与奖励")
        save_debug("5_1_video_process")
        time.sleep(10) # 模拟等待视频播放时间
        
        save_debug("7_1_final_check")
        print("🎉 任务执行完毕")

        _watcher_stop.set()
        browser.close()

if __name__ == "__main__":
    run()
```[cite: 1]
