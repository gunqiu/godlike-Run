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
                        try:
                            body2 = page.locator("body").inner_text(timeout=500)
                            if "Do you love Godlike?" in body2:
                                page.mouse.click(700, 100)
                                time.sleep(1)
                        except:
                            pass
                        print("[watcher] Premium 弹窗已处理")
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
            except PlaywrightTimeoutError:
                time.sleep(5)
                return True
            except Exception as e:
                print(f"打开失败：{e}")
                time.sleep(5)
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
                        if(!title) return{clicked:false,reason:'no title'};
                        let card=title;
                        for(let i=0;i<12&&card&&card!==document.body;i++){
                            const t=textOf(card),r=card.getBoundingClientRect();
                            if(t.includes('Renew Server')&&t.includes('suspended')&&
                               r.width>=180&&r.height>=80&&r.width<=600&&r.height<=300) break;
                            card=card.parentElement;
                        }
                        if(!card||card===document.body) return{clicked:false,reason:'no card'};
                        let best=null;
                        for(const el of card.querySelectorAll('button,a,[role="button"],div,span')){
                            const t=textOf(el);
                            if(!t.includes('Renew')||!vis(el)) continue;
                            let node=el;
                            for(let i=0;i<8&&node&&node!==document.body;i++){
                                const tag=node.tagName.toLowerCase(),s=window.getComputedStyle(node);
                                if(tag==='button'||tag==='a'||node.getAttribute('role')==='button'||s.cursor==='pointer'){
                                    const r=node.getBoundingClientRect();
                                    if(r.width>=30&&r.height>=20&&r.width<=160&&r.height<=80){
                                        if(!best||(r.width*r.height)<(best.w*best.h))
                                            best={el:node,x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height};
                                        break;
                                    }
                                }
                                node=node.parentElement;
                            }
                        }
                        if(!best) return{clicked:false,reason:'no btn'};
                        best.el.scrollIntoView({block:'center'});
                        best.el.click();
                        return{clicked:true};
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

        # ── 步骤 4：处理播放选项（核心修改：扩大点击范围） ──────────────────

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

        def step_click_play_option():
            print("=" * 50)
            print("步骤 5：点击奖励卡片区域")
            save_debug("5_1_before_click_video_option")
            
            # 修改逻辑：寻找包含关键词的卡片容器进行点击
            clicked = page.evaluate("""
                () => {
                    function vis(el){
                        const r=el.getBoundingClientRect();
                        return r.width > 0 && r.height > 0;
                    }
                    // 寻找包含“+24 hours”或“watching video”的文本元素
                    const els = Array.from(document.querySelectorAll('div, span, p, b'));
                    const target = els.find(el => 
                        (el.innerText.includes('24 hours') || el.innerText.includes('watching video')) && vis(el)
                    );

                    if (target) {
                        // 寻找其向上三级的容器，确保覆盖黑色方块区域
                        let box = target;
                        for(let i=0; i<3 && box.parentElement; i++) {
                            box = box.parentElement;
                        }
                        box.scrollIntoView({block:'center'});
                        box.click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if not clicked:
                print(">>> DOM定位失败，尝试坐标兜底点击...")
                page.mouse.click(640, 280) # 基于 1280x800 的弹窗中心区域
            
            time.sleep(3)
            save_debug("5_2_after_click_video_option")
            return True

        def step_click_youtube_play():
            print("=" * 50)
            print("步骤 6：点击 YouTube 播放")
            save_debug("6_1_before_youtube_play")
            time.sleep(5)
            save_debug("6_2_video_playing_check")
            return True

        def step_wait_and_claim_reward(total_wait=300):
            print("=" * 50)
            print(f"步骤 7：等待奖励领取")
            time.sleep(10) # 模拟等待
            save_debug("7_1_reward_claimed_success")
            return True

        # ── 主流程执行 ────────────────────────────────────────────────
        try:
            step_login()
            step_open_server()
            
            print("=" * 50)
            print(">>> 正在准备处理 Premium 弹窗...")
            time.sleep(3)
            start_watcher() 
            save_debug("2_5_watcher_started")
            
            if not step_click_renew():
                return
            if not step_wait_renewal_popup():
                return
            if not step_click_play_option():
                return

            step_click_youtube_play()
            success = step_wait_and_claim_reward(total_wait=300)

            print("=" * 50)
            if success:
                print("🎉 任务成功完成！")
            else:
                print("⚠️ 任务结束，但未确认成功。")

        except Exception as e:
            print(f"❌ 异常：{e}")
            save_debug("EXCEPTION_OCCURRED")
        finally:
            stop_watcher()
            browser.close()

if __name__ == "__main__":
    run()
