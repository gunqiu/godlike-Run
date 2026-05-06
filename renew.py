import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
            # 如果你想人工接着操作，可以改成：
            # headless=False,
            # slow_mo=300
        )

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
                print(f"已保存截图：{name}")
            except Exception as e:
                print(f"保存截图失败：{e}")

        def safe_goto(url, name):
            print(f"正在打开{name}：{url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(5)
                print(f"{name}已打开")
                return True
            except PlaywrightTimeoutError:
                print(f"{name}打开超时，但页面可能已经出来了，继续执行")
                time.sleep(5)
                return True
            except Exception as e:
                print(f"{name}打开异常：{e}")
                time.sleep(5)
                return False

        def close_premium_popup_only_if_blocks():
            """
            只处理中间 Premium 大弹窗。
            不处理左下角问卷。
            """
            try:
                body_text = page.locator("body").inner_text(timeout=1000)
            except:
                body_text = ""

            if (
                "Do you love Godlike?" not in body_text
                and "Claim -50% Off" not in body_text
                and "I'm fine with waiting in the queue" not in body_text
            ):
                return

            print("检测到 Premium 大弹窗，尝试关闭")

            try:
                page.mouse.click(905, 128)
                time.sleep(1)
            except:
                pass

            try:
                page.mouse.click(640, 615)
                time.sleep(1)
            except:
                pass

            try:
                page.keyboard.press("Escape")
                time.sleep(1)
            except:
                pass

        def find_and_click_renew():
            """
            找 Renew Server 卡片里的 Renew 按钮。
            这一段保留，因为你现在已经成功点到了 Renew。
            """
            print("开始寻找 Renew 按钮...")

            result = page.evaluate(
                """
                () => {
                    function isVisible(el) {
                        if (!el) return false;

                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);

                        return (
                            rect.width > 0 &&
                            rect.height > 0 &&
                            rect.bottom > 0 &&
                            rect.right > 0 &&
                            rect.top < window.innerHeight &&
                            rect.left < window.innerWidth &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            style.opacity !== '0'
                        );
                    }

                    function textOf(el) {
                        return (el.innerText || el.textContent || '').trim();
                    }

                    function findClickable(el) {
                        let node = el;

                        for (let i = 0; i < 8 && node && node !== document.body; i++) {
                            const tag = node.tagName ? node.tagName.toLowerCase() : '';
                            const role = node.getAttribute ? node.getAttribute('role') : '';
                            const style = window.getComputedStyle(node);

                            if (
                                tag === 'button' ||
                                tag === 'a' ||
                                role === 'button' ||
                                style.cursor === 'pointer' ||
                                typeof node.onclick === 'function'
                            ) {
                                return node;
                            }

                            node = node.parentElement;
                        }

                        return el;
                    }

                    const all = Array.from(document.querySelectorAll('body *'));

                    let renewTitle = null;

                    for (const el of all) {
                        const text = textOf(el);

                        if (text === 'Renew Server' && isVisible(el)) {
                            renewTitle = el;
                            break;
                        }
                    }

                    if (!renewTitle) {
                        return {
                            clicked: false,
                            reason: '没有找到 Renew Server 标题'
                        };
                    }

                    let card = renewTitle;

                    for (let i = 0; i < 12 && card && card !== document.body; i++) {
                        const rect = card.getBoundingClientRect();
                        const text = textOf(card);

                        if (
                            text.includes('Renew Server') &&
                            text.includes('free server will be suspended') &&
                            rect.width >= 180 &&
                            rect.height >= 80 &&
                            rect.width <= 600 &&
                            rect.height <= 300
                        ) {
                            break;
                        }

                        card = card.parentElement;
                    }

                    if (!card || card === document.body) {
                        return {
                            clicked: false,
                            reason: '没有找到 Renew Server 卡片'
                        };
                    }

                    const cardRect = card.getBoundingClientRect();

                    const inside = Array.from(card.querySelectorAll('button, a, [role="button"], div, span'));

                    let candidates = [];

                    for (const el of inside) {
                        const text = textOf(el);

                        if (text.includes('Renew') && isVisible(el)) {
                            const clickable = findClickable(el);
                            const rect = clickable.getBoundingClientRect();

                            if (
                                rect.width >= 30 &&
                                rect.height >= 20 &&
                                rect.width <= 160 &&
                                rect.height <= 80
                            ) {
                                candidates.push({
                                    el: clickable,
                                    x: rect.x + rect.width / 2,
                                    y: rect.y + rect.height / 2,
                                    width: rect.width,
                                    height: rect.height,
                                    text: textOf(clickable)
                                });
                            }
                        }
                    }

                    if (candidates.length > 0) {
                        candidates.sort((a, b) => (a.width * a.height) - (b.width * b.height));

                        const target = candidates[0];
                        const topEl = document.elementFromPoint(target.x, target.y);

                        const notCovered =
                            topEl &&
                            (
                                topEl === target.el ||
                                target.el.contains(topEl) ||
                                topEl.contains(target.el)
                            );

                        if (!notCovered) {
                            return {
                                clicked: false,
                                reason: 'Renew 按钮被遮挡',
                                x: target.x,
                                y: target.y,
                                topTag: topEl ? topEl.tagName : null,
                                topText: topEl ? textOf(topEl) : null
                            };
                        }

                        target.el.scrollIntoView({
                            block: 'center',
                            inline: 'center'
                        });

                        target.el.click();

                        return {
                            clicked: true,
                            method: 'DOM Renew button',
                            x: target.x,
                            y: target.y,
                            text: target.text,
                            cardX: cardRect.x,
                            cardY: cardRect.y,
                            cardWidth: cardRect.width,
                            cardHeight: cardRect.height
                        };
                    }

                    return {
                        clicked: false,
                        reason: '没有找到可点击的 Renew 按钮',
                        cardX: cardRect.x,
                        cardY: cardRect.y,
                        cardWidth: cardRect.width,
                        cardHeight: cardRect.height,
                        cardText: textOf(card)
                    };
                }
                """
            )

            print(f"点击 Renew 结果：{result}")

            if result and result.get("clicked"):
                time.sleep(3)
                save_debug("after_click_renew.png")
                return True

            return False

        def wait_and_click_renew(max_seconds=40):
            print("开始检测当前画面，只要 Renew 没被挡住就点击...")

            start = time.time()

            while time.time() - start < max_seconds:
                close_premium_popup_only_if_blocks()

                if find_and_click_renew():
                    return True

                print("Renew 暂时没点到，1 秒后重试")
                time.sleep(1)

            print("超过 40 秒还没有点到 Renew")
            save_debug("renew_click_failed.png")
            return False

        def wait_for_renew_method_popup(max_seconds=25):
            print("等待 Choose Renewal Method 弹窗...")

            start = time.time()

            while time.time() - start < max_seconds:
                try:
                    body_text = page.locator("body").inner_text(timeout=1000)

                    if "Choose Renewal Method" in body_text:
                        print("已经检测到 Choose Renewal Method 弹窗")
                        save_debug("renew_method_popup.png")
                        return True
                except:
                    pass

                time.sleep(1)

            print("没有检测到 Choose Renewal Method 弹窗")
            save_debug("renew_method_popup_not_found.png")
            return False

        def click_watch_video_option_until_video_panel():
            """
            点击 Get +24 hours by watching video。
            已根据你的日志确认：
            第三个固定点 x=405, y=365 有效。
            """
            print("准备点击 Get +24 hours by watching video...")

            save_debug("before_click_watch_video_option.png")

            fixed_points = [
                (405, 315),
                (410, 320),
                # 这个点是你这次验证成功的点
                (405, 365),
            ]

            for index, (x, y) in enumerate(fixed_points):
                print(f"尝试固定坐标点击播放广告区域第 {index + 1} 个点：x={x}, y={y}")

                try:
                    page.mouse.move(x, y)
                    time.sleep(0.2)
                    page.mouse.down()
                    time.sleep(0.2)
                    page.mouse.up()

                    time.sleep(3)

                    save_debug(f"after_click_watch_fixed_{index + 1}.png")

                    try:
                        body_text = page.locator("body").inner_text(timeout=1000)
                    except:
                        body_text = ""

                    if (
                        "Watch Video to Renew" in body_text
                        or "Watch the video for 240 seconds" in body_text
                        or "YouTube" in body_text
                    ):
                        print("已经进入 Watch Video to Renew 页面")
                        save_debug("watch_video_to_renew_ready.png")
                        return True

                except Exception as e:
                    print(f"点击播放广告区域失败：{e}")

            print("没有进入 Watch Video to Renew 页面")
            save_debug("watch_video_option_click_failed.png")
            return False

        # ──────────────────────────────────────────────────────────────
        # 以下为新增部分
        # ──────────────────────────────────────────────────────────────

        def click_youtube_play_button():
            """
            进入 Watch Video to Renew 页面后，点击 YouTube 播放器中间的红色播放按钮。
            策略：先找 iframe，再在 iframe 内点击播放按钮；找不到就用固定坐标兜底。
            """
            print("尝试点击 YouTube 播放器中间的红色播放按钮...")
            save_debug("before_click_youtube_play.png")

            # ── 策略 1：通过 DOM 找 YouTube iframe，在 iframe 内点击播放按钮 ──
            try:
                # 找到页面内的 YouTube iframe
                yt_frame = None
                for frame in page.frames:
                    if "youtube.com" in frame.url or "youtube-nocookie.com" in frame.url:
                        yt_frame = frame
                        break

                if yt_frame:
                    print(f"找到 YouTube iframe：{yt_frame.url}")
                    # 尝试点击大播放按钮（.ytp-large-play-button 或 .ytp-play-button）
                    for selector in [
                        ".ytp-large-play-button",
                        "button.ytp-play-button",
                        "[aria-label='Play']",
                        ".ytp-cued-thumbnail-overlay-image",
                    ]:
                        try:
                            btn = yt_frame.locator(selector).first
                            if btn.is_visible(timeout=3000):
                                btn.click(force=True)
                                print(f"通过 iframe selector '{selector}' 点击了播放按钮")
                                time.sleep(3)
                                save_debug("after_click_youtube_play_iframe.png")
                                return True
                        except:
                            pass
            except Exception as e:
                print(f"iframe 内点击播放失败：{e}")

            # ── 策略 2：固定坐标兜底（视频播放器通常居中显示） ──
            # 根据 1280×800 的视口，YouTube 播放器大约在弹窗正中央
            fallback_points = [
                (480, 400),
                (480, 380),
                (480, 420),
                (500, 400),
            ]
            for idx, (x, y) in enumerate(fallback_points):
                print(f"固定坐标点击 YouTube 播放按钮 第{idx+1}次：x={x}, y={y}")
                try:
                    page.mouse.click(x, y)
                    time.sleep(3)
                    save_debug(f"after_click_youtube_play_fixed_{idx+1}.png")

                    # 检测视频是否已经开始播放（iframe 的 paused 属性）
                    is_playing = page.evaluate(
                        """
                        () => {
                            const videos = document.querySelectorAll('video');
                            for (const v of videos) {
                                if (!v.paused && v.currentTime > 0) return true;
                            }
                            // 检查 iframe 内的 video（同域限制，可能拿不到，忽略报错）
                            try {
                                const iframes = document.querySelectorAll('iframe');
                                for (const f of iframes) {
                                    const doc = f.contentDocument || f.contentWindow.document;
                                    const vids = doc.querySelectorAll('video');
                                    for (const v of vids) {
                                        if (!v.paused && v.currentTime > 0) return true;
                                    }
                                }
                            } catch(e) {}
                            return false;
                        }
                        """
                    )
                    if is_playing:
                        print("检测到视频已开始播放")
                        return True
                except Exception as e:
                    print(f"固定坐标点击失败：{e}")

            # 即使无法确认是否播放，也返回 True 继续流程
            print("无法确认视频是否播放，继续后续流程")
            return True

        def watch_video_and_wait_for_reward(total_wait=270):
            """
            在视频播放过程中持续监控页面，
            在 240~260 秒之间出现 "Get +24 hours" 弹窗时立即点击。
            total_wait：最长等待秒数（留出 10 秒余量）。
            返回 True 表示成功点击了奖励按钮。
            """
            print(f"开始监控视频播放，最长等待 {total_wait} 秒...")
            start = time.time()
            reward_clicked = False

            while True:
                elapsed = time.time() - start
                remaining = total_wait - elapsed

                if remaining <= 0:
                    print(f"已等待 {total_wait} 秒，未检测到奖励弹窗，退出监控")
                    break

                # 每隔 5 秒截一次图（仅在关键时间段附近）
                if 230 <= elapsed <= 270 and int(elapsed) % 10 == 0:
                    save_debug(f"watch_progress_{int(elapsed)}s.png")

                try:
                    body_text = page.locator("body").inner_text(timeout=1000)
                except:
                    body_text = ""

                # ── 检测奖励弹窗 ──
                # 关键词：根据实际弹窗文字调整，常见有：
                # "Get +24 hours" / "+24 hours" / "Claim" / "You've earned"
                reward_keywords = [
                    "Get +24 hours",
                    "+24 hours",
                    "Claim your",
                    "You've earned",
                    "server renewed",
                    "Server Renewed",
                ]
                found_keyword = next(
                    (kw for kw in reward_keywords if kw in body_text), None
                )

                if found_keyword:
                    print(f"[{int(elapsed)}s] 检测到奖励弹窗关键词：'{found_keyword}'")
                    save_debug(f"reward_popup_detected_{int(elapsed)}s.png")

                    # 尝试通过 DOM 找并点击按钮
                    clicked = page.evaluate(
                        """
                        () => {
                            function textOf(el) {
                                return (el.innerText || el.textContent || '').trim();
                            }
                            function isVisible(el) {
                                if (!el) return false;
                                const rect = el.getBoundingClientRect();
                                const style = window.getComputedStyle(el);
                                return (
                                    rect.width > 0 && rect.height > 0 &&
                                    rect.top < window.innerHeight && rect.left < window.innerWidth &&
                                    style.display !== 'none' &&
                                    style.visibility !== 'hidden' &&
                                    style.opacity !== '0'
                                );
                            }

                            const keywords = ['Get +24 hours', '+24 hours', 'Claim', 'Collect'];
                            const all = Array.from(document.querySelectorAll(
                                'button, a, [role="button"], div, span'
                            ));

                            for (const kw of keywords) {
                                for (const el of all) {
                                    if (textOf(el).includes(kw) && isVisible(el)) {
                                        const rect = el.getBoundingClientRect();
                                        // 排除太大的容器元素，只取按钮级别
                                        if (rect.width > 20 && rect.width < 400 &&
                                            rect.height > 20 && rect.height < 120) {
                                            el.scrollIntoView({ block: 'center' });
                                            el.click();
                                            return {
                                                clicked: true,
                                                keyword: kw,
                                                text: textOf(el),
                                                x: rect.x + rect.width / 2,
                                                y: rect.y + rect.height / 2
                                            };
                                        }
                                    }
                                }
                            }
                            return { clicked: false };
                        }
                        """
                    )

                    print(f"奖励按钮点击结果：{clicked}")

                    if clicked and clicked.get("clicked"):
                        print("成功点击了奖励按钮！")
                        save_debug("reward_clicked_success.png")
                        reward_clicked = True
                        break
                    else:
                        # DOM 没找到，用固定坐标兜底（弹窗通常居中）
                        print("DOM 未找到按钮，尝试固定坐标点击弹窗中央...")
                        for fx, fy in [(480, 430), (480, 450), (480, 410)]:
                            page.mouse.click(fx, fy)
                            time.sleep(1)
                            save_debug(f"reward_fixed_click_{fx}_{fy}.png")

                            try:
                                body_after = page.locator("body").inner_text(timeout=1000)
                            except:
                                body_after = ""

                            # 如果弹窗消失了，说明点击成功
                            if not any(kw in body_after for kw in reward_keywords):
                                print("弹窗已消失，判断为点击成功")
                                reward_clicked = True
                                break

                        if reward_clicked:
                            save_debug("reward_clicked_success.png")
                            break

                time.sleep(2)

            if not reward_clicked:
                save_debug("reward_not_clicked.png")

            return reward_clicked

        try:
            # 1. 登录
            print("正在登录...")

            safe_goto(LOGIN_URL, "登录页")

            try:
                login_switch = page.get_by_text("Through Login/Password")

                if login_switch.is_visible(timeout=3000):
                    login_switch.click(force=True)
                    print("已切换到账号密码登录")
            except:
                print("没有看到 Through Login/Password，继续登录")

            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])

            page.locator('button:has-text("Login")').first.click()

            page.wait_for_url(lambda url: "login" not in url, timeout=25000)

            print("登录成功！")

            # 2. 打开服务器页面
            print("前往管理页...")

            safe_goto(SERVER_URL, "服务器管理页")

            time.sleep(3)

            save_debug("after_server_page.png")

            # 3. 点击 Renew
            clicked_renew = wait_and_click_renew(max_seconds=40)

            if not clicked_renew:
                print("任务失败：没有点击到 Renew")
                return

            # 4. 等待 Choose Renewal Method 弹窗
            if not wait_for_renew_method_popup(max_seconds=25):
                print("任务失败：点击 Renew 后没有弹出 Choose Renewal Method")
                return

            # 5. 点击 Get +24 hours by watching video（进入视频页）
            if not click_watch_video_option_until_video_panel():
                print("任务失败：没有进入 Watch Video to Renew 页面")
                return

            print("已到达 Watch Video to Renew 页面，等待 3 秒后点击播放按钮...")
            time.sleep(3)

            # 6. 点击 YouTube 播放器中间的红色播放按钮
            click_youtube_play_button()

            print("播放按钮已点击，开始监控奖励弹窗（视频约需 240 秒）...")

            # 7. 监控视频播放，在 240~260 秒之间点击弹窗中的 Get +24 hours
            success = watch_video_and_wait_for_reward(total_wait=270)

            if success:
                print("任务完成：已成功点击奖励按钮，服务器续期 +24 小时！")
            else:
                print("任务警告：未能确认点击奖励按钮，请检查截图排查原因")

            save_debug("final_state.png")

        except Exception as e:
            print(f"异常：{e}")
            save_debug("error_exception.png")

        finally:
            browser.close()


if __name__ == "__main__":
    run()
