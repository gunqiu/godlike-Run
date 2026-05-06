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
            不处理左下角问卷，不点问卷。
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

            # Premium 大弹窗右上角 X
            try:
                page.mouse.click(905, 128)
                time.sleep(1)
            except:
                pass

            # Premium 大弹窗底部 I'm fine...
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
            核心：只找 Renew Server 卡片里的 Renew 按钮。
            如果没有挡住，就点击。
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

                    // 1. 找 Renew Server 标题
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

                    // 2. 找 Renew Server 卡片
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

                    // 3. 在卡片里面找 Renew 按钮
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

                    // 4. 如果找到了真正按钮，点击按钮中心
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

                    // 5. 如果文字按钮找不到，按卡片位置计算 Renew 按钮中心
                    // 适配两种布局：Renew 卡片在左侧 或 Renew 卡片在右侧
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

                        const topText = textOf(topEl);

                        // 这个点必须还在 Renew Server 卡片里面，避免乱点
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
                            topText,
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
            """
            最多等 40 秒。
            只要 Renew 没被挡住，就点。
            不跑十几分钟。
            """
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
            等待弹出 Choose Renewal Method。
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
            点击 Choose Renewal Method 弹窗里的：
            Get +24 hours by watching video
            """
            print("准备点击 Get +24 hours by watching video...")

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

                    const all = Array.from(document.querySelectorAll('body *'));

                    // 1. 找弹窗标题
                    let title = null;

                    for (const el of all) {
                        if (textOf(el).includes('Choose Renewal Method') && isVisible(el)) {
                            title = el;
                            break;
                        }
                    }

                    if (!title) {
                        return {
                            clicked: false,
                            reason: '没有找到 Choose Renewal Method 标题'
                        };
                    }

                    // 2. 找弹窗容器
                    let modal = title;

                    for (let i = 0; i < 12 && modal && modal !== document.body; i++) {
                        const rect = modal.getBoundingClientRect();
                        const text = textOf(modal);

                        if (
                            text.includes('Choose Renewal Method') &&
                            text.includes('watching video') &&
                            rect.width >= 300 &&
                            rect.height >= 200
                        ) {
                            break;
                        }

                        modal = modal.parentElement;
                    }

                    if (!modal || modal === document.body) {
                        return {
                            clicked: false,
                            reason: '没有找到 Renewal 弹窗容器'
                        };
                    }

                    const modalRect = modal.getBoundingClientRect();

                    // 3. 找 “Get +24 hours by watching video” 文字区域
                    let videoText = null;

                    for (const el of Array.from(modal.querySelectorAll('body *'))) {
                        const text = textOf(el);

                        if (
                            text.includes('Get +24 hours') &&
                            text.includes('watching video') &&
                            isVisible(el)
                        ) {
                            videoText = el;
                            break;
                        }
                    }

                    if (videoText) {
                        let clickable = videoText;

                        // 往上找比较大的可点击区域
                        for (let i = 0; i < 8 && clickable && clickable !== modal; i++) {
                            const rect = clickable.getBoundingClientRect();
                            const style = window.getComputedStyle(clickable);
                            const tag = clickable.tagName ? clickable.tagName.toLowerCase() : '';
                            const role = clickable.getAttribute ? clickable.getAttribute('role') : '';

                            if (
                                tag === 'button' ||
                                tag === 'a' ||
                                role === 'button' ||
                                style.cursor === 'pointer' ||
                                rect.width >= 120 && rect.height >= 80
                            ) {
                                break;
                            }

                            clickable = clickable.parentElement;
                        }

                        const rect = clickable.getBoundingClientRect();
                        const x = rect.x + rect.width / 2;
                        const y = rect.y + rect.height / 2;

                        clickable.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: x, clientY: y }));
                        clickable.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: x, clientY: y }));
                        clickable.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
                        clickable.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
                        clickable.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y }));

                        return {
                            clicked: true,
                            method: 'video text area',
                            x,
                            y,
                            text: textOf(clickable)
                        };
                    }

                    // 4. 如果文字找不到，直接点击弹窗左侧播放区域
                    // 从你的 11.png 看，播放区域在弹窗左半部分
                    const fallbackPoints = [
                        {
                            x: modalRect.x + modalRect.width * 0.28,
                            y: modalRect.y + modalRect.height * 0.45
                        },
                        {
                            x: modalRect.x + modalRect.width * 0.30,
                            y: modalRect.y + modalRect.height * 0.55
                        },
                        {
                            x: modalRect.x + modalRect.width * 0.22,
                            y: modalRect.y + modalRect.height * 0.40
                        }
                    ];

                    for (const point of fallbackPoints) {
                        const x = point.x;
                        const y = point.y;
                        const el = document.elementFromPoint(x, y);

                        if (!el) continue;

                        el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: x, clientY: y }));
                        el.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: x, clientY: y }));
                        el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
                        el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
                        el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y }));

                        return {
                            clicked: true,
                            method: 'modal fallback point',
                            x,
                            y,
                            tag: el.tagName,
                            text: textOf(el)
                        };
                    }

                    return {
                        clicked: false,
                        reason: '没有找到可点击的视频选项'
                    };
                }
                """
            )

            print(f"点击播放广告选项结果：{result}")

            if result and result.get("clicked"):
                time.sleep(5)
                save_debug("after_click_watch_video_option.png")
                return True

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

            # 4. 等待播放广告弹窗
            if not wait_for_renew_method_popup(max_seconds=25):
                print("任务失败：点击 Renew 后没有弹出 Choose Renewal Method")
                return

            # 5. 点击 Get +24 hours by watching video
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
