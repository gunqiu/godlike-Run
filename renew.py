import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
            # 如果想看浏览器操作，可以改成：
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
            只找 Renew Server 卡片里的 Renew 按钮。
            现在这部分已经成功了，保持不动。
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

                    const fallbackPoints = [
                        {
                            x: cardRect.x + 62,
                            y: cardRect.y + cardRect.height - 36
                        },
                        {
                            x: cardRect.x + 55,
                            y: cardRect.y + cardRect.height - 42
                        },
                        {
                            x: cardRect.x + 70,
                            y: cardRect.y + cardRect.height - 34
                        }
                    ];

                    for (const point of fallbackPoints) {
                        const x = point.x;
                        const y = point.y;
                        const topEl = document.elementFromPoint(x, y);

                        if (!topEl) continue;

                        if (!card.contains(topEl) && topEl !== card) {
                            continue;
                        }

                        topEl.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: x, clientY: y }));
                        topEl.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: x, clientY: y }));
                        topEl.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
                        topEl.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
                        topEl.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y }));

                        return {
                            clicked: true,
                            method: 'card coordinate',
                            x,
                            y,
                            topTag: topEl.tagName,
                            topText: textOf(topEl),
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
            """
            等待 Choose Renewal Method 弹窗。
            """
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

        def click_watch_video_option():
            """
            重点修复：
            不再点击弹窗大容器中心。
            专门点击左侧播放三角形 / Get +24 hours by watching video 区域。
            """
            print("准备点击 Get +24 hours by watching video...")

            time.sleep(1)

            save_debug("before_click_watch_video_option.png")

            # 方法 1：根据弹窗位置动态计算播放区域
            try:
                modal_info = page.evaluate(
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

                        const all = Array.from(document.querySelectorAll('body *'));

                        let title = null;

                        for (const el of all) {
                            if (textOf(el).includes('Choose Renewal Method') && isVisible(el)) {
                                title = el;
                                break;
                            }
                        }

                        if (!title) {
                            return {
                                found: false,
                                reason: '没有找到 Choose Renewal Method 标题'
                            };
                        }

                        let modal = title;

                        for (let i = 0; i < 12 && modal && modal !== document.body; i++) {
                            const rect = modal.getBoundingClientRect();
                            const text = textOf(modal);

                            if (
                                text.includes('Choose Renewal Method') &&
                                text.includes('watching video') &&
                                rect.width >= 300 &&
                                rect.height >= 200 &&
                                rect.width <= 800 &&
                                rect.height <= 600
                            ) {
                                break;
                            }

                            modal = modal.parentElement;
                        }

                        if (!modal || modal === document.body) {
                            return {
                                found: false,
                                reason: '没有找到 Renewal 弹窗容器'
                            };
                        }

                        const rect = modal.getBoundingClientRect();

                        return {
                            found: true,
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            text: textOf(modal)
                        };
                    }
                    """
                )

                print(f"Renewal 弹窗位置：{modal_info}")

                if modal_info and modal_info.get("found"):
                    mx = modal_info["x"]
                    my = modal_info["y"]
                    mw = modal_info["width"]
                    mh = modal_info["height"]

                    # 这些点都在弹窗左侧播放卡片区域。
                    # 从你的截图看，播放三角形大概在弹窗左侧中上部。
                    points = [
                        # 播放三角形附近
                        (mx + mw * 0.25, my + mh * 0.38),

                        # Get +24 hours by watching video 文字中心
                        (mx + mw * 0.25, my + mh * 0.55),

                        # 左侧卡片整体中心
                        (mx + mw * 0.25, my + mh * 0.48),

                        # 稍微偏右一点，防止三角形位置变化
                        (mx + mw * 0.32, my + mh * 0.42),

                        # 稍微偏下一点
                        (mx + mw * 0.32, my + mh * 0.56),
                    ]

                    for index, point in enumerate(points):
                        x, y = point

                        print(f"尝试点击播放广告区域第 {index + 1} 个点：x={x}, y={y}")

                        page.mouse.move(x, y)
                        time.sleep(0.2)
                        page.mouse.down()
                        time.sleep(0.2)
                        page.mouse.up()

                        time.sleep(3)

                        save_debug(f"after_click_watch_point_{index + 1}.png")

                        # 点完后检查弹窗是否消失，或者页面文字是否变化
                        try:
                            body_text = page.locator("body").inner_text(timeout=1000)
                        except:
                            body_text = ""

                        if "Choose Renewal Method" not in body_text:
                            print("Choose Renewal Method 弹窗已经消失，说明播放选项可能点击成功")
                            return True

                        # 如果弹窗还在，但页面可能已经开始加载广告，也继续尝试下一个点
                        print("弹窗还在，继续尝试下一个播放区域点")

            except Exception as e:
                print(f"动态点击播放区域失败：{e}")

            # 方法 2：根据你截图的固定坐标兜底
            # 你的截图中播放三角形大约在 x=405, y=315 附近。
            fixed_points = [
                (405, 315),
                (410, 320),
                (405, 365),
                (420, 360),
                (395, 355),
            ]

            for index, point in enumerate(fixed_points):
                x, y = point

                try:
                    print(f"尝试固定坐标点击播放广告区域第 {index + 1} 个点：x={x}, y={y}")

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

                    if "Choose Renewal Method" not in body_text:
                        print("弹窗已经消失，播放广告选项点击成功")
                        return True

                except Exception as e:
                    print(f"固定坐标点击播放广告失败：{e}")

            print("播放广告选项可能没有点击成功")
            save_debug("watch_video_option_click_failed.png")
            return False

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

            # 5. 点击左侧播放广告选项
            if click_watch_video_option():
                print("任务完成：已经点击播放广告选项")
            else:
                print("任务失败：没有点击到播放广告选项")

        except Exception as e:
            print(f"异常：{e}")
            save_debug("error_exception.png")

        finally:
            browser.close()


if __name__ == "__main__":
    run()
