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
            """
            进入服务器页面后一直跑，每 2 秒检查一次。
            只处理 "Do you love Godlike?" 这个弹窗，其他弹窗不管。
            视频播放后也继续跑，直到主流程结束才停。
            """
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
                                // 优先点 "I'm fine with waiting in the queue"
                                for(const el of document.querySelectorAll('button,a,[role="button"],div,span')){
                                    if(textOf(el).includes("I'm fine with waiting")&&vis(el)){
                                        el.click(); return;
                                    }
                                }
                                // 兜底：点右上角 X 按钮
                                for(const el of document.querySelectorAll('button,[role="button"]')){
                                    const t=textOf(el);
                                    if((t==='×'||t==='✕'||t==='X'||t==='x'||t==='close')&&vis(el)){
                                        el.click(); return;
                                    }
                                }
                                // 固定坐标兜底（弹窗右上角约 x=700, y=100）
                                // 注：evaluate 里无法用 page.mouse，只能 DOM
                            }
                        """)
                        time.sleep(1.5)
                        # 如果还在，用坐标点
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
            t = threading.Thread(target=_premium_watcher, daemon=True)
            t.start()
            return t

        def stop_watcher():
            _watcher_stop.set()

        # ── 工具函数 ──────────────────────────────────────────────────

        def save_debug(name):
            try:
                page.screenshot(path=name, full_page=True)
                print(f"[截图] {name}")
            except Exception as e:
                print(f"[截图失败] {name}: {e}")

        def fail(step_name):
            save_debug(f"FAIL_{step_name}.png")
            print(f"❌ 失败于步骤：{step_name}")

        def safe_goto(url, name):
            print(f"打开 {name}...")
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
            print("步骤 1：登录")
            safe_goto(LOGIN_URL, "登录页")
            try:
                sw = page.get_by_text("Through Login/Password")
                if sw.is_visible(timeout=3000):
                    sw.click(force=True)
            except:
                pass
            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])
            page.locator('button:has-text("Login")').first.click()
            page.wait_for_url(lambda url: "login" not in url, timeout=25000)
            print("✅ 登录成功")

        # ── 步骤 2：打开服务器页面（启动弹窗侦测）───────────────────

        def step_open_server():
            print("=" * 50)
            print("步骤 2：打开服务器页面，启动 Premium 弹窗侦测")
            safe_goto(SERVER_URL, "服务器管理页")
            time.sleep(3)
            start_watcher()   # ← 进入服务器页面后立即启动后台侦测
            print("✅ 服务器页面已打开，弹窗侦测已启动")

        # ── 步骤 3：点击 Renew ────────────────────────────────────────

        def step_click_renew(max_seconds=40):
            print("=" * 50)
            print("步骤 3：点击 Renew 按钮")
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
                        const top=document.elementFromPoint(best.x,best.y);
                        if(top&&!best.el.contains(top)&&!top.contains(best.el))
                            return{clicked:false,reason:'covered'};
                        best.el.scrollIntoView({block:'center'});
                        best.el.click();
                        return{clicked:true,x:best.x,y:best.y};
                    }
                """)
                if result and result.get("clicked"):
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
                if "Choose Renewal Method" in get_body_text():
                    print("✅ Choose Renewal Method 弹窗已出现")
                    return True
                time.sleep(1)
            fail("renewal_popup")
            return False

        # ── 步骤 5：点击 ▶ ───────────────────────────────────────────

        def step_click_play_option():
            print("=" * 50)
            print("步骤 5：点击 ▶ Get +24 hours by watching video")

            clicked = page.evaluate("""
                () => {
                    function vis(el){
                        const r=el.getBoundingClientRect(),s=window.getComputedStyle(el);
                        return r.width>0&&r.height>0&&r.top<window.innerHeight&&
                               s.display!=='none'&&s.visibility!=='hidden'&&s.opacity!=='0';
                    }
                    function textOf(el){return(el.innerText||el.textContent||'').trim();}
                    let container=null;
                    for(const el of document.querySelectorAll('body *')){
                        const t=textOf(el);
                        if(t.includes('Get +24 hours')&&t.includes('watching')&&vis(el)){
                            if(!container||el.contains(container)) container=el;
                        }
                    }
                    if(container){
                        let node=container;
                        for(let i=0;i<12&&node&&node!==document.body;i++){
                            const tag=node.tagName.toLowerCase(),s=window.getComputedStyle(node);
                            if(tag==='button'||tag==='a'||node.getAttribute('role')==='button'||s.cursor==='pointer'){
                                const r=node.getBoundingClientRect();
                                if(r.width>20&&r.height>20){
                                    node.scrollIntoView({block:'center'});
                                    node.click();
                                    return{clicked:true,method:'text-parent'};
                                }
                            }
                            node=node.parentElement;
                        }
                        container.click();
                        return{clicked:true,method:'container-direct'};
                    }
                    for(const dialog of document.querySelectorAll('[role="dialog"],.modal,[class*="modal"],[class*="popup"]')){
                        if(!vis(dialog)||!textOf(dialog).includes('Choose Renewal')) continue;
                        for(const btn of dialog.querySelectorAll('button,[role="button"],svg,[class*="play"]')){
                            if(!vis(btn)) continue;
                            const r=btn.getBoundingClientRect();
                            if(r.width>10&&r.height>10){btn.click();return{clicked:true,method:'dialog-svg'};}
                        }
                    }
                    return{clicked:false};
                }
            """)
            print(f"DOM 点击结果：{clicked}")
            time.sleep(2)

            if "Choose Renewal Method" not in get_body_text():
                print("✅ 视频页已打开")
                return True

            for x, y in [(375, 280), (375, 260), (375, 300), (380, 275), (370, 285)]:
                print(f"固定坐标 ({x},{y})...")
                page.mouse.click(x, y)
                time.sleep(2)
                if "Choose Renewal Method" not in get_body_text():
                    print(f"✅ 坐标 ({x},{y}) 有效")
                    return True

            fail("click_play_option")
            return False

        # ── 步骤 6：点击 YouTube 播放按钮 ────────────────────────────

        def step_click_youtube_play():
            print("=" * 50)
            print("步骤 6：点击 YouTube 播放按钮")
            time.sleep(3)

            try:
                for frame in page.frames:
                    if "youtube.com" in frame.url or "youtube-nocookie.com" in frame.url:
                        print("找到 YouTube iframe")
                        for sel in [".ytp-large-play-button", "button.ytp-play-button",
                                    "[aria-label='Play']", "[aria-label='play']"]:
                            try:
                                btn = frame.locator(sel).first
                                if btn.is_visible(timeout=2000):
                                    btn.click(force=True)
                                    print(f"✅ iframe 播放已点击：{sel}")
                                    time.sleep(2)
                                    return True
                            except:
                                pass
            except Exception as e:
                print(f"iframe 失败：{e}")

            clicked = page.evaluate("""
                () => {
                    function vis(el){
                        const r=el.getBoundingClientRect(),s=window.getComputedStyle(el);
                        return r.width>0&&r.height>0&&r.top<window.innerHeight&&
                               s.display!=='none'&&s.visibility!=='hidden'&&s.opacity!=='0';
                    }
                    for(const sel of['button[aria-label*="play" i]','.ytp-large-play-button',
                                     '.ytp-play-button','div[class*="video"] button','div[class*="player"] button']){
                        for(const el of document.querySelectorAll(sel)){
                            if(vis(el)){el.click();return{ok:true,sel};}
                        }
                    }
                    for(const btn of document.querySelectorAll('button,[role="button"]')){
                        if(!vis(btn)) continue;
                        if(btn.querySelectorAll('svg,path,polygon').length>0){
                            const r=btn.getBoundingClientRect();
                            if(r.width>20&&r.width<200&&r.height>20&&r.height<200){
                                btn.click();return{ok:true,sel:'svg-btn'};
                            }
                        }
                    }
                    return{ok:false};
                }
            """)
            if clicked and clicked.get("ok"):
                print("✅ DOM 播放已点击")
                time.sleep(2)
                return True

            for x, y in [(487, 262), (487, 245), (487, 275)]:
                page.mouse.click(x, y)
                time.sleep(2)
                playing = page.evaluate("""
                    ()=>{for(const v of document.querySelectorAll('video'))
                           if(!v.paused&&v.currentTime>0) return true; return false;}
                """)
                if playing:
                    print("✅ 视频播放中")
                    return True

            print("⚠️ 未确认播放，继续监控")
            return True

        # ── 步骤 7：等待奖励弹窗并点击 ───────────────────────────────

        def step_wait_and_claim_reward(total_wait=300):
            print("=" * 50)
            print(f"步骤 7：等待奖励弹窗（最长 {total_wait} 秒）")
            start = time.time()
            reward_keywords = [
                "Get +24 hours", "+24 hours", "Claim your",
                "You've earned", "server renewed", "Server Renewed", "Congratulations"
            ]

            while True:
                elapsed = time.time() - start
                if elapsed >= total_wait:
                    fail("reward_timeout")
                    return False

                body = get_body_text()
                found = next((kw for kw in reward_keywords
                              if kw in body and "Do you love Godlike?" not in body), None)

                if found:
                    print(f"[{int(elapsed)}s] ✅ 奖励关键词：'{found}'")
                    clicked = page.evaluate("""
                        () => {
                            function textOf(el){return(el.innerText||el.textContent||'').trim();}
                            function vis(el){
                                const r=el.getBoundingClientRect(),s=window.getComputedStyle(el);
                                return r.width>0&&r.height>0&&r.top<window.innerHeight&&
                                       s.display!=='none'&&s.visibility!=='hidden'&&s.opacity!=='0';
                            }
                            for(const kw of['Get +24 hours','+24 hours','Claim','Collect','Congratulations']){
                                for(const el of document.querySelectorAll('button,a,[role="button"],div,span')){
                                    if(textOf(el).includes(kw)&&vis(el)){
                                        const r=el.getBoundingClientRect();
                                        if(r.width>20&&r.width<400&&r.height>20&&r.height<120){
                                            el.scrollIntoView({block:'center'});
                                            el.click();
                                            return{clicked:true,kw,text:textOf(el)};
                                        }
                                    }
                                }
                            }
                            return{clicked:false};
                        }
                    """)
                    print(f"奖励点击：{clicked}")
                    if clicked and clicked.get("clicked"):
                        print("🎉 成功点击奖励！")
                        return True
                    for fx, fy in [(490, 430), (490, 450), (490, 410)]:
                        page.mouse.click(fx, fy)
                        time.sleep(1)
                    if not any(kw in get_body_text() for kw in reward_keywords):
                        print("🎉 弹窗消失，判断成功")
                        return True
                    fail("reward_click_failed")
                    return False

                if int(elapsed) % 60 == 0 and elapsed > 0:
                    print(f"[{int(elapsed)}s] 等待奖励弹窗...")

                time.sleep(2)

        # ── 主流程 ────────────────────────────────────────────────────
        try:
            step_login()
            step_open_server()   # 启动弹窗侦测线程

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
                print("🎉 任务完成：服务器已续期 +24 小时！")
            else:
                print("⚠️ 任务未完成，请查看截图")

        except Exception as e:
            print(f"❌ 异常：{e}")
            save_debug("FAIL_exception.png")
        finally:
            stop_watcher()
            browser.close()


if __name__ == "__main__":
    run()
