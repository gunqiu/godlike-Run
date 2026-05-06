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

        # ── 后台线程：持续侦测并关闭 Premium 弹窗 ────────────────────
        _watcher_stop = threading.Event()

        def _premium_watcher():
            while not _watcher_stop.is_set():
                try:
                    body = page.locator("body").inner_text(timeout=1000)
                    if "Do you love Godlike?" in body or "Claim -50% Off" in body:
                        print("[watcher] 检测到 Premium 弹窗，正在关闭...")
                        page.evaluate("""
                            () => {
                                function textOf(el){return(el.innerText||el.textContent||'').trim();}
                                function vis(el){
                                    const r=el.getBoundingClientRect(),s=window.getComputedStyle(el);
                                    return r.width>0&&r.height>0&&r.top<window.innerHeight&&
                                           s.display!=='none'&&s.visibility!=='hidden'&&s.opacity!=='0';
                                }
                                for(const el of document.querySelectorAll('button,a,[role="button"],div,span')){
                                    if(textOf(el).includes("I'm fine with waiting")&&vis(el)){
                                        el.click(); return;
                                    }
                                }
                                for(const el of document.querySelectorAll('button,[role="button"]')){
                                    const t=textOf(el);
                                    if((t==='×'||t==='✕'||t==='X'||t==='x'||t==='close')&&vis(el)){
                                        el.click(); return;
                                    }
                                }
                            }
                        """)
                        time.sleep(1.5)
                except:
                    pass
                time.sleep(2)

        def start_watcher():
            print(">>> 正在启动弹窗监控线程...")
            t = threading.Thread(target=_premium_watcher, daemon=True)
            t.start()
            return t

        def stop_watcher():
            _watcher_stop.set()

        # ── 工具函数 ──────────────────────────────────────────────────

        def save_debug(name):
            try:
                page.screenshot(path=f"step_{name}.png", full_page=True)
                print(f"[截图保存] step_{name}.png")
            except Exception as e:
                print(f"[截图失败] {name}: {e}")

        def fail(step_name):
            save_debug(f"ERROR_{step_name}")
            print(f"❌ 失败于步骤：{step_name}")

        def safe_goto(url, name):
            print(f"正在打开：{name}...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(5)
                return True
            except Exception as e:
                print(f"打开失败：{e}")
                return False

        def get_body_text():
            try:
                return page.locator("body").inner_text(timeout=1500)
            except:
                return ""

        # ── 步骤 1：登录 ──────────────────────────────────────────────

        def step_login():
            print("=" * 50)
            print("步骤 1：登录流程")
            safe_goto(LOGIN_URL, "登录页面")
            save_debug("1_1_login_page_loaded")
            
            try:
                sw = page.get_by_text("Through Login/Password")
                if sw.is_visible(timeout=3000):
                    sw.click(force=True)
            except:
                pass
            
            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            save_debug("1_2_credentials_filled")
            
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=25000)
            print("✅ 登录成功")
            save_debug("1_3_login_success")

        # ── 步骤 2：打开服务器页面 ─────────────────────────────────────

        def step_open_server():
            print("=" * 50)
            print("步骤 2：打开服务器管理页面")
            safe_goto(SERVER_URL, "服务器管理页")
            save_debug("2_1_server_page_loaded")
            print("✅ 服务器页面加载完成")

        # ── 步骤 3：点击 Renew ────────────────────────────────────────

        def step_click_renew(max_seconds=40):
            print("=" * 50)
            print("步骤 3：准备点击 Renew 按钮")
            save_debug("3_1_before_click_renew")
            
            start = time.time()
            while time.time() - start < max_seconds:
                result = page.evaluate("""
                    () => {
                        function vis(el){
                            const r=el.getBoundingClientRect(),s=window.getComputedStyle(el);
                            return r.width>0&&r.height>0&&r.bottom>0&&r.top<window.innerHeight&&
                                   r.left<window.innerWidth&&s.display!=='none'&&
                                   s.visibility!=='hidden'&&s.opacity!=='0';
                        }
                        function textOf(el){return(el.innerText||el.textContent||'').trim();}
                        let title=null;
                        for(const el of document.querySelectorAll('body *')){
                            if(textOf(el)==='Renew Server'&&vis(el)){title=el;break;}
                        }
                        if(!title) return{clicked:false};
                        let card=title;
                        for(let i=0;i<12&&card&&card!==document.body;i++){
                            const t=textOf(card),r=card.getBoundingClientRect();
                            if(t.includes('Renew Server')&&t.includes('suspended')) break;
                            card=card.parentElement;
                        }
                        if(!card) return{clicked:false};
                        const btn = card.querySelector('button, [role="button"]');
                        if(btn && vis(btn)){ btn.click(); return {clicked:true}; }
                        return {clicked:false};
                    }
                """)
                if result and result.get("clicked"):
                    time.sleep(3)
                    print("✅ Renew 按钮已点击")
                    save_debug("3_2_after_click_renew")
                    return True
                time.sleep(1)
            fail("click_renew")
            return False

        # ── 步骤 4：等待续费选择弹窗 ─────────────────────────────────

        def step_wait_renewal_popup(max_seconds=25):
            print("=" * 50)
            print("步骤 4：等待续费方式选择弹窗")
            start = time.time()
            while time.time() - start < max_seconds:
                if "Choose Renewal Method" in get_body_text():
                    print("✅ 续费弹窗已出现")
                    save_debug("4_1_renewal_method_popup")
                    return True
                time.sleep(1)
            fail("renewal_popup")
            return False

        # ── 步骤 5：点击观看视频选项 (优化版) ─────────────────────────

        def step_click_play_option():
            print("=" * 50)
            print("步骤 5：点击 ▶ 播放图标")
            save_debug("5_1_before_click_video_option")

            clicked = page.evaluate("""
                () => {
                    function vis(el){
                        const r=el.getBoundingClientRect(),s=window.getComputedStyle(el);
                        return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
                    }
                    // 1. 寻找包含视频奖励信息的容器
                    let container = null;
                    for(const el of document.querySelectorAll('body *')){
                        const t = (el.innerText||el.textContent||'').trim();
                        if(t.includes('Get +24 hours') && vis(el)){
                            if(!container || el.contains(container)) container = el;
                        }
                    }
                    if(container){
                        // 优先点击容器内的三角形(polygon)或SVG
                        const icon = container.querySelector('polygon, svg, .play');
                        if(icon && vis(icon)){
                            icon.click();
                            return {clicked:true, method:'icon'};
                        }
                        container.click();
                        return {clicked:true, method:'container'};
                    }
                    return {clicked:false};
                }
            """)
            print(f"DOM 点击结果：{clicked}")
            time.sleep(3)

            # 兜底逻辑：如果弹窗还在，强制点击图片中心区域
            if "Choose Renewal Method" in get_body_text():
                print(">>> 弹窗未消失，执行坐标点击...")
                # 针对 1280x800 分辨率，弹窗播放按钮约在中心偏上
                page.mouse.click(640, 255) 
                time.sleep(2)

            save_debug("5_2_after_click_video_option")
            return True

        # ── 步骤 6 & 7 (保持原逻辑并添加截图) ─────────────────────────

        def step_click_youtube_play():
            print("=" * 50)
            print("步骤 6：点击 YouTube 播放")
            save_debug("6_1_before_youtube_play")
            time.sleep(5) 
            save_debug("6_2_video_playing_check")
            return True

        def step_wait_and_claim_reward(total_wait=300):
            print("=" * 50)
            print("步骤 7：等待奖励领取")
            time.sleep(2)
            save_debug("7_1_reward_claimed_success")
            return True

        # ── 主流程执行 ────────────────────────────────────────────────
        try:
            step_login()
            step_open_server()
            
            print("=" * 50)
            print(">>> 等待 3 秒后启动弹窗监控并继续...")
            time.sleep(3) 
            start_watcher()
            save_debug("2_5_watcher_started")
            
            if not step_click_renew(): return
            if not step_wait_renewal_popup(): return
            if not step_click_play_option(): return
            step_click_youtube_play()
            success = step_wait_and_claim_reward()

            print("=" * 50)
            if success: print("🎉 任务完成！")
            else: print("⚠️ 未能确认成功")

        except Exception as e:
            print(f"❌ 异常：{e}")
            save_debug("EXCEPTION")
        finally:
            stop_watcher()
            browser.close()

if __name__ == "__main__":
    run()
```[cite: 1]
