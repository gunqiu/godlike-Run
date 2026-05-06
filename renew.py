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
            """任务在某步失败时调用：截图并退出。"""
            save_debug(f"FAIL_{step_name}.png")
            print(f"❌ 任务失败于步骤：{step_name}")

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

        # ── 专门处理图片中的 Premium 推广弹窗 ────────────────

        def close_specific_premium_popup():
            """
            检测并关闭图片中显示的 'Do you love Godlike?' 弹窗。
            """
            try:
                # 检查页面是否包含特定推广文字
                body_text = get_body_text()
                if "Do you love Godlike?" in body_text or "Claim -50% Off" in body_text:
                    print("[检测到推广弹窗] 尝试关闭...")
                    
                    # 尝试寻找弹窗右上角的 X 按钮 (通常是 dialog 里的第一个 button 或带 svg 的按钮)
                    # 这里的选择器组合了多种可能的情况
                    close_btn = page.locator('div[role="dialog"] button:has(svg), .modal-header button, button:has-text("✕")').first
                    
                    if close_btn.is_visible(timeout=2000):
                        close_btn.click()
                        print("✅ 已点击右上角 X 关闭推广弹窗")
                        time.sleep(1.5)
                        return True
                    
                    # 备选：点击底部的 "I'm fine with waiting..."
                    fine_btn = page.get_by_text("I'm fine with waiting", exact=False)
                    if fine_btn.is_visible(timeout=1000):
                        fine_btn.click()
                        print("✅ 已点击 'I'm fine' 文本关闭弹窗")
                        time.sleep(1.5)
                        return True
                        
                    # 最后兜底：按 ESC 键
                    page.keyboard.press("Escape")
                    print("⌨️ 已发送 Escape 键尝试关闭")
            except:
                pass
            return False

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
                # 实时监控弹窗
                close_specific_premium_popup()
                
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
                # 关键：这里也要检测，因为点击 Renew 后常弹出推广窗挡住目标
                close_specific_premium_popup()
                
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
                    return{clicked:false};
                }
            """)
            print(f"DOM 点击结果：{clicked}")
            time.sleep(2)

            if "Choose Renewal Method" not in get_body_text():
                print("✅ 视频页已打开")
                return True

            # 坐标兜底
            for x, y in [(375, 280), (375, 260)]:
                page.mouse.click(x, y)
                time.sleep(2)
                if "Choose Renewal Method" not in get_body_text():
                    return True

            fail("click_play_option")
            return False

        # ── 步骤 6：点击 YouTube 播放按钮 ────────────────────────────

        def step_click_youtube_play():
            print("=" * 50)
            print("步骤 6：点击 YouTube 播放按钮")
            time.sleep(3)
            # iframe 逻辑保留
            try:
                for frame in page.frames:
                    if "youtube.com" in frame.url:
                        btn = frame.locator(".ytp-large-play-button").first
                        if btn.is_visible(timeout=2000):
                            btn.click(force=True)
                            print("✅ iframe 播放成功")
                            return True
            except:
                pass
            print("⚠️ 未发现 YouTube 播放按钮，可能已自动播放")
            return True

        # ── 步骤 7：等待奖励弹窗并点击 ───────────────────────────────

        def step_wait_and_claim_reward(total_wait=300):
            print("=" * 50)
            print(f"步骤 7：等待奖励（最长 {total_wait} 秒）")
            start = time.time()
            reward_keywords = ["Get +24 hours", "+24 hours", "Claim", "Congratulations"]

            while True:
                elapsed = time.time() - start
                if elapsed >= total_wait:
                    fail("reward_timeout")
                    return False
                
                # 持续清理推广弹窗
                close_specific_premium_popup()

                body = get_body_text()
                # 排除掉推广弹窗的文字干扰，只找真正的奖励按钮
                if any(kw in body for kw in reward_keywords) and "Do you love Godlike?" not in body:
                    print(f"[{int(elapsed)}s] ✅ 发现奖励！")
                    clicked = page.evaluate("""
                        () => {
                            function textOf(el){return(el.innerText||el.textContent||'').trim();}
                            function vis(el){
                                const r=el.getBoundingClientRect(),s=window.getComputedStyle(el);
                                return r.width>0&&r.height>0&&s.display!=='none';
                            }
                            const kws = ['Get +24 hours','+24 hours','Claim','Collect'];
                            for(const kw of kws){
                                for(const el of document.querySelectorAll('button,a,[role="button"]')){
                                    if(textOf(el).includes(kw)&&vis(el)){
                                        el.click(); return true;
                                    }
                                }
                            }
                            return false;
                        }
                    """)
                    if clicked:
                        print("🎉 奖励已领取！")
                        return True

                time.sleep(3)

        # ── 执行主流程 ────────────────────────────────────────────────
        try:
            step_login()
            step_open_server()
            if step_click_renew():
                if step_wait_renewal_popup():
                    if step_click_play_option():
                        step_click_youtube_play()
                        success = step_wait_and_claim_reward()
                        if success:
                            print("=" * 50)
                            print("🎉 恭喜！服务器续期成功。")
        except Exception as e:
            print(f"❌ 运行异常: {e}")
            save_debug("FAIL_exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
