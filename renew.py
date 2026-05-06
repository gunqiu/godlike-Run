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
                    # 监控并关闭可能遮挡的 Premium 弹窗
                    if "I'm fine with waiting" in page.content():
                        page.get_by_text("I'm fine with waiting").click()
                except: pass
                time.sleep(2)

        def save_debug(name):
            try: page.screenshot(path=f"step_{name}.png", full_page=True)
            except: pass

        # ── 步骤 1：登录 ──────────────────────────────────────────────
        print("=" * 50)
        print("步骤 1：登录流程")
        page.goto(LOGIN_URL, wait_until="networkidle")
        
        # 修复：显式等待邮箱输入框出现[cite: 2]
        page.wait_for_selector('input[type="email"]', timeout=30000)
        page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
        page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
        page.locator('button:has-text("Login")').first.click()
        page.wait_for_url(lambda url: "login" not in url, timeout=25000)
        print("✅ 登录成功")

        # ── 步骤 2：打开服务器页面 ─────────────────────────────────────
        print("=" * 50)
        print("步骤 2：打开管理页面")
        page.goto(SERVER_URL, wait_until="domcontentloaded")
        time.sleep(5)
        
        t = threading.Thread(target=_premium_watcher, daemon=True)
        t.start()

        # ── 步骤 3：点击 Renew 按钮 ──────────────────────────────────
        print("=" * 50)
        print("步骤 3：寻找并点击 Renew 按钮")
        page.wait_for_selector('button:has-text("Renew")', timeout=20000)
        page.get_by_text("Renew", exact=True).first.click()
        time.sleep(5)

        # ── 步骤 4：处理续费弹窗（核心改动：扩大点击范围） ──────────────
        print("=" * 50)
        print("步骤 4：处理视频领取区域")
        save_debug("4_0_before_click")

        # 逻辑：不点三角形，直接点包含文字的黑色大方块[cite: 1]
        clicked = page.evaluate("""
            () => {
                function vis(el){
                    const r=el.getBoundingClientRect();
                    return r.width > 0 && r.height > 0;
                }
                // 寻找包含特定文本的元素[cite: 1]
                const targets = Array.from(document.querySelectorAll('div, span, p'));
                const cardText = targets.find(el => 
                    el.innerText.includes('Get +24 hours') && vis(el)
                );

                if (cardText) {
                    // 向上寻找最近的容器 div[cite: 1]
                    let container = cardText.parentElement;
                    while (container && container.tagName !== 'DIV') {
                        container = container.parentElement;
                    }
                    if (container) {
                        container.click();
                        return { status: 'success', method: 'container_click' };
                    }
                }
                return { status: 'failed' };
            }
        """)
        
        print(f">>> 区域点击尝试：{clicked}")
        time.sleep(3)
        
        # 兜底：如果没点开，尝试直接点击弹窗正中心[cite: 1]
        if "Choose Renewal Method" in page.content():
            print(">>> 弹窗未消失，执行中心位置强点击...")
            page.mouse.click(640, 280)
            time.sleep(2)
        
        save_debug("4_1_after_click")

        # ── 步骤 5：完成 ──────────────────────────────────────────────
        print("=" * 50)
        print("正在确认任务...")
        time.sleep(10)
        save_debug("5_final")
        print("🎉 脚本运行结束")

        _watcher_stop.set()
        browser.close()

if __name__ == "__main__":
    run()
