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
            """
            不使用 networkidle，避免网站一直有后台请求导致超时。
            """
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

        def close_premium_popup_only():
            """
            只处理中间大的 Premium 50% 弹窗。
            不再处理左下角问卷。
            """
            try:
                result = page.evaluate(
                    """
                    () => {
                        const text = document.body.innerText || '';

                        if (
                            !text.includes('Do you love Godlike?') &&
                            !text.includes('Claim -50% Off') &&
                            !text.includes("I'm fine with waiting in the queue")
                        ) {
                            return {
                                found: false,
                                action: '没有 Premium 大弹窗'
                            };
                        }

                        // 优先点击右上角 X，按照当前截图位置
                        const x = 905;
                        const y = 128;
                        const el = document.elementFromPoint(x, y);

                        if (el) {
                            el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
                            el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
                            el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y }));

                            return {
                                found: true,
                                action: '已点击 Premium X',
                                tag: el.tagName,
                                text: el.innerText || el.textContent || ''
                            };
                        }

                        return {
                            found: true,
                            action: '发现 Premium 大弹窗，但没有点到 X'
                        };
                    }
                    """
                )

                print(f"Premium 弹窗检测结果：{result}")
                time.sleep(1)
            except Exception as e:
                print(f"关闭 Premium 弹窗失败：{e}")

            try:
                page.keyboard.press("Escape")
                time.sleep(0.5)
            except:
                pass

        def find_renew_button_info():
            """
            检测 Renew 按钮是否存在、是否可见、是否被遮挡。
            重点：只找 Renew Server 卡片里的 Renew，不找其他页面元素。
            """
            try:
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

                        // 第一步：找 Renew Server 卡片
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
                                found: false,
                                reason: '没有找到 Renew Server 标题'
                            };
                        }

                        let card = renewTitle;

                        for (let i = 0; i < 10 && card && card !== document.body; i++) {
                            const rect = card.getBoundingClientRect();
                            const text = textOf(card);

                            if (
                                text.includes('Renew Server') &&
                                text.includes('free server will be suspended') &&
                                rect.width >= 180 &&
                                rect.height >= 80 &&
                                rect.width <= 500 &&
                                rect.height <= 250
                            ) {
                                break;
                            }

                            card = card.parentElement;
                        }

                        if (!card || card === document.body) {
                            return {
                                found: false,
                                reason: '没有找到 Renew Server 卡片'
                            };
                        }

                        const cardRect = card.getBoundingClientRect();

                        // 第二步：优先在卡片里面找文字等于 Renew 的按钮
                        const inside = Array.from(card.querySelectorAll('button, a, [role="button"], div, span'));

                        for (const el of inside) {
                            const text = textOf(el);

                            if (text === 'Renew' && isVisible(el)) {
                                const clickable = findClickable(el);
                                const rect = clickable.getBoundingClientRect();

                                const x = rect.x + rect.width / 2;
                                const y = rect.y + rect.height / 2;

                                const topEl = document.elementFromPoint(x, y);

                                const notCovered =
                                    topEl &&
                                    (
                                        topEl === clickable ||
                                        clickable.contains(topEl) ||
                                        topEl.contains(clickable)
                                    );

                                return {
                                    found: true,
                                    method: 'text Renew',
                                    x,
                                    y,
                                    width: rect.width,
                                    height: rect.height,
                                    notCovered,
                                    topTag: topEl ? topEl.tagName : null,
                                    topText: topEl ? textOf(topEl) : null,
                                    buttonText: textOf(clickable)
                                };
                            }
                        }

                        // 第三步：如果文字找不到，就根据 Renew Server 卡片位置计算按钮中心
                        // 从截图看，Renew 按钮在卡片左下区域
                        const x = cardRect.x + 52;
                        const y = cardRect.y + cardRect.height - 34;

                        const topEl = document.elementFromPoint(x, y);
                        const topText = topEl ? textOf(topEl) : '';

                        const looksLikeRenew =
                            topEl &&
                            (
                                topText.includes('Renew') ||
                                textOf(card).includes('Renew Server')
                            );

                        return {
                            found: true,
                            method: 'card coordinate',
                            x,
                            y,
                            width: 80,
                            height: 40,
                            notCovered: looksLikeRenew,
                            topTag: topEl ? topEl.tagName : null,
                            topText,
                            cardText: textOf(card)
                        };
                    }
                    """
                )

                return result
            except Exception as e:
                return {
                    "found": False,
                    "reason": f"JS 检测 Renew 异常：{e}"
                }

        def click_renew_when_not_blocked(max_wait_seconds=90):
            """
            检测当前画面。
            只要 Renew 按钮没被挡住，就点击。
            最多等待 90 秒，不会无限跑十几分钟。
            """
            print("开始检测 Renew 按钮是否可点击...")

            start = time.time()
            last_print = 0

            while time.time() - start < max_wait_seconds:
                info = find_renew_button_info()

                now = time.time()
                if now - last_print > 3:
                    print(f"Renew 检测结果：{info}")
                    last_print = now

                if info.get("found") and info.get("notCovered"):
                    x = info["x"]
                    y = info["y"]

                    print(f"Renew 按钮没有被挡住，准备点击：x={x}, y={y}")

                    page.mouse.move(x, y)
                    time.sleep(0.2)
                    page.mouse.down()
                    time.sleep(0.2)
                    page.mouse.up()

                    time.sleep(5)

                    save_debug("after_click_renew.png")

                    print("已经点击 Renew")
                    return True

                # 如果是 Premium 大弹窗挡住，就只关 Premium 大弹窗
                body_text = ""
                try:
                    body_text = page.locator("body").inner_text(timeout=1000)
                except:
                    pass

                if (
                    "Do you love Godlike?" in body_text or
                    "Claim -50% Off" in body_text or
                    "I'm fine with waiting in the queue" in body_text
                ):
                    print("检测到 Premium 大弹窗，尝试关闭")
                    close_premium_popup_only()
                else:
                    print("Renew 还不能点击，等待 1 秒后再检测")

                time.sleep(1)

            print("等待 Renew 可点击超时，没有点击成功")
            save_debug("renew_not_clicked_timeout.png")
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

            # 3. 只检测 Renew 按钮，不乱点别的
            clicked = click_renew_when_not_blocked(max_wait_seconds=90)

            if clicked:
                print("任务完成：Renew 已点击")
            else:
                print("任务失败：没有点击到 Renew")

        except Exception as e:
            print(f"异常：{e}")
            save_debug("error_exception.png")

        finally:
            browser.close()


if __name__ == "__main__":
    run()
