import os
import time
import threading
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 固定视口大小，确保坐标点击的一致性
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # --- 弹窗监控逻辑 (保持不变) ---
        _watcher_stop = threading.Event()
        def _premium_watcher():
            while not _watcher_stop.is_set():
                try:
                    body = page.locator("body").inner_text(timeout=1000)
                    if "Do you love Godlike?" in body or "Claim -50% Off" in body:
                        page.evaluate("""() => {
                            const btns = Array.from(document.querySelectorAll('button, a, span'));
                            const close = btns.find(b => b.innerText.includes("I'm fine with waiting") || b.innerText === '×');
                            if(close) close.click();
                        }""")
                except: pass
                time.sleep(2)

        def save_debug(name):
            page.screenshot(path=f"step_{name}.png", full_page=True)
            print(f"[截图已保存] step_{name}.png")

        # --- 步骤 1 & 2 & 3 (保持你原本稳定的逻辑) ---
        def step_login():
            page.goto(LOGIN_URL)
            try:
                page.get_by_text("Through Login/Password").click(timeout=3000)
            except: pass
            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=25000)

        def step_open_server():
            page.goto(SERVER_URL)
            time.sleep(5)

        def step_click_renew():
            page.evaluate("() => { const b = Array.from(document.querySelectorAll('button, span')).find(e => e.innerText.includes('Renew')); if(b) b.click(); }")
            time.sleep(3)

        # --- 步骤 5：强化点击逻辑 (重点修改) ---
        def step_click_play_option():
            print("=" * 50)
            print("步骤 5：执行多点覆盖点击策略")
            save_debug("5_1_attempting_clicks")
            
            # 策略 A: 针对截图中的黑色卡片区域进行中心点击 (1280x800下的坐标)
            # 黑色弹窗中心大致在 (640, 280)
            print(">>> 尝试坐标点击 (中心及周边)...")
            coords = [(640, 280), (640, 300), (640, 250), (600, 280), (680, 280)]
            for x, y in coords:
                page.mouse.click(x, y)
                time.sleep(0.5)
            
            # 策略 B: 使用 JS 穿透所有层级，强制点击包含 "24 hours" 字样的最上层容器
            page.evaluate("""
                () => {
                    const findBox = () => {
                        const all = document.querySelectorAll('div, span, b');
                        const target = Array.from(all).find(el => el.innerText.includes('24 hours'));
                        if (!target) return null;
                        // 向上寻找具有点击属性或深色背景的父容器
                        let curr = target;
                        for(let i=0; i<4; i++) {
                            if(curr.parentElement) curr = curr.parentElement;
                        }
                        return curr;
                    };
                    const box = findBox();
                    if (box) {
                        const rect = box.getBoundingClientRect();
                        const x = rect.left + rect.width / 2;
                        const y = rect.top + rect.height / 2;
                        // 派发原生点击事件
                        ['mousedown', 'mouseup', 'click'].forEach(type => {
                            box.dispatchEvent(new MouseEvent(type, {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                clientX: x,
                                clientY: y
                            }));
                        });
                    }
                }
            """)
            
            time.sleep(5)
            save_debug("5_2_after_enhanced_clicks")
            
            # 检查弹窗是否还在，如果还在说明没点到
            body_text = page.locator("body").inner_text()
            if "Choose Renewal Method" in body_text:
                print("⚠️ 警告：检测到弹窗仍未消失，可能需要更大幅度的坐标调整。")
                return False
            print("✅ 弹窗已消失，点击可能成功。")
            return True

        # --- 执行主流程 ---
        try:
            step_login()
            step_open_server()
            
            t = threading.Thread(target=_premium_watcher, daemon=True)
            t.start()
            
            step_click_renew()
            if "Choose Renewal Method" in page.locator("body").inner_text():
                step_click_play_option()
            
            print(">>> 流程结束。")
        finally:
            _watcher_stop.set()
            browser.close()

if __name__ == "__main__":
    run()
```[cite: 3]

### 为什么这次更有效？
1.  **坐标阵列点击**：我在弹窗中心点 $(640, 280)$ 周边安排了 5 个点击点。由于你提到“点三角形周边也行”，这种阵列点击可以极大提高触发概率[cite: 3]。
2.  **事件穿透**：有些网页组件会拦截标准的 `.click()`。我改用 JS 模拟 `mousedown` 和 `mouseup` 组合，这能绕过绝大多数前端拦截[cite: 3]。
3.  **父容器回溯**：代码会从文字 `24 hours` 开始向上找 4 层父级容器进行点击，确保点在那个巨大的“黑色方块”上，而不是细小的文字线条上[cite: 3]。
