import os
import time
import threading
from playwright.sync_api import sync_playwright

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

        _watcher_stop = threading.Event()

        def _premium_watcher():
            while not _watcher_stop.is_set():
                try:
                    body = page.locator("body").inner_text(timeout=1000)
                    if "Do you love Godlike?" in body or "Claim -50% Off" in body:
                        page.evaluate("""
                            () => {
                                function textOf(el){return(el.innerText||el.textContent||'').trim();}
                                for(const el of document.querySelectorAll('button,a,span,div')){
                                    if(textOf(el).includes("I'm fine with waiting")){
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
        page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
        page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
        page.locator('button:has-text("Login")').first.click()
        page.wait_for_url(lambda url: "login" not in url, timeout=25000)
        print("✅ 登录成功")

        # ── 步骤 2：打开服务器页面 ─────────────────────────────────────
        print("=" * 50)
        print("步骤 2：打开服务器管理页面")
        page.goto(SERVER_URL, wait_until="domcontentloaded")
        time.sleep(5)
        
        print(">>> 启动弹窗监控...")
        start_watcher()

        # ── 步骤 3：点击 Renew 按钮 ──────────────────────────────────
        print("=" * 50)
        print("步骤 3：点击 Renew 按钮")
        page.evaluate("""
            () => {
                const els = document.querySelectorAll('button, [role="button"]');
                for(const el of els){
                    if(el.innerText.includes('Renew')){ el.click(); return; }
                }
            }
        """)
        time.sleep(4)

        # ── 步骤 4：点击观看视频区域（扩大范围） ───────────────────────
        print("=" * 50)
        print("步骤 4：处理续费弹窗（点击视频播放区域）")
        
        popup_detected = False
        for _ in range(15):
            if "Choose Renewal Method" in get_body_text():
                popup_detected = True
                print("✅ 续费弹窗已出现")
                break
            time.sleep(1)

        if popup_detected:
            save_debug("4_1_popup_check")
            print(">>> 正在定位并点击视频奖励区域...")
            
            # 逻辑：寻找包含关键词的元素，并点击它所在的容器
            clicked = page.evaluate("""
                () => {
                    function vis(el){
                        const r=el.getBoundingClientRect();
                        return r.width > 0 && r.height > 0;
                    }
                    // 寻找包含“+24 hours”或“watching video”的文本
                    const elements = Array.from(document.querySelectorAll('div, span, p, b'));
                    const target = elements.find(el => 
                        (el.innerText.includes('24 hours') || el.innerText.includes('watching video')) && vis(el)
                    );

                    if (target) {
                        // 向上找几层父级，确保点到的是大的黑色背景区域
                        let box = target;
                        for(let i=0; i<3; i++) {
                            if(box.parentElement) box = box.parentElement;
                        }
                        box.click();
                        return {ok: true, text: target.innerText.substring(0,20)};
                    }
                    return {ok: false};
                }
            """)
            print(f"区域点击尝试: {clicked}")
            time.sleep(3)
            
            # 如果弹窗还在，执行坐标点击（基于 1280x800 中心区域）
            if "Choose Renewal Method" in get_body_text():
                print(">>> 弹窗未消失，执行中心坐标兜底点击...")
                page.mouse.click(640, 300) 
                time.sleep(2)
            
            save_debug("4_2_after_area_click")

        # ── 步骤 5：完成 ──────────────────────────────────────────────
        print("=" * 50)
        print("正在确认任务状态...")
        time.sleep(5)
        save_debug("5_final")
        print("🎉 流程运行结束")

        _watcher_stop.set()
        browser.close()

if __name__ == "__main__":
    run()
