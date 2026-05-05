import os
import time
from playwright.sync_api import sync_playwright


LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"


def run():
    with sync_playwright() as p:
        # 如果你想看到浏览器运行过程，把 headless=True 改成 headless=False
        browser = p.chromium.launch(
            headless=True
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
                print(f"截图失败：{e}")

        def kill_advertising():
            """
            尽量关闭或者移除 Godlike 的 50% Off 弹窗。
            这个函数不会影响主流程，即使失败也会继续往下跑。
            """
            print("正在清理广告弹窗...")

            time.sleep(1)

            # 方案 1：用 JS 点击 “I'm fine with waiting in the queue”
            try:
                result = page.evaluate(
                    """
                    () => {
                        const targetText = "I'm fine with waiting in the queue";

                        function isVisible(el) {
                            if (!el) return false;
                            const rect = el.getBoundingClientRect();
                            const style = window.getComputedStyle(el);
                            return (
                                rect.width > 0 &&
                                rect.height > 0 &&
                                style.display !== 'none' &&
                                style.visibility !== 'hidden' &&
                                style.opacity !== '0'
                            );
                        }

                        function findClickable(el) {
                            let node = el;
                            for (let i = 0; i < 6 && node && node !== document.body; i++) {
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

                        for (const el of all) {
                            const text = (el.innerText || el.textContent || '').trim();

                            if (text === targetText && isVisible(el)) {
                                const clickable = findClickable(el);
                                clickable.click();
                                return true;
                            }
                        }

                        return false;
                    }
                    """
                )

                if result:
                    print("已点击底部关闭文字")
                    time.sleep(1)
                    return
            except Exception as e:
                print(f"点击底部关闭文字失败：{e}")

            # 方案 2：点击弹窗右上角 X，使用动态位置，不再用死坐标
            try:
                result = page.evaluate(
                    """
                    () => {
                        const keywords = [
                            'Do you love Godlike?',
                            'Switch to Premium today',
                            'Claim -50% Off'
                        ];

                        function isVisible(el) {
                            if (!el) return false;
                            const rect = el.getBoundingClientRect();
                            const style = window.getComputedStyle(el);
                            return (
                                rect.width > 0 &&
                                rect.height > 0 &&
                                style.display !== 'none' &&
                                style.visibility !== 'hidden' &&
                                style.opacity !== '0'
                            );
                        }

                        const all = Array.from(document.querySelectorAll('body *'));

                        let keywordEl = null;

                        for (const el of all) {
                            const text = el.innerText || el.textContent || '';
                            if (isVisible(el) && keywords.some(k => text.includes(k))) {
                                keywordEl = el;
                                break;
                            }
                        }

                        if (!keywordEl) {
                            return { clicked: false, reason: 'no modal keyword' };
                        }

                        let bestBox = null;
                        let node = keywordEl;

                        for (let i = 0; i < 10 && node && node !== document.body; i++) {
                            const rect = node.getBoundingClientRect();

                            if (
                                rect.width >= 250 &&
                                rect.height >= 200 &&
                                rect.width <= window.innerWidth * 0.95 &&
                                rect.height <= window.innerHeight * 0.95
                            ) {
                                bestBox = {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                };
                            }

                            node = node.parentElement;
                        }

                        if (!bestBox) {
                            return { clicked: false, reason: 'no good box' };
                        }

                        const x = bestBox.x + bestBox.width - 20;
                        const y = bestBox.y + 20;

                        const target = document.elementFromPoint(x, y);

                        if (target) {
                            target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
                            target.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
                            target.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y }));
                            return { clicked: true, x, y, tag: target.tagName, text: target.innerText || target.textContent || '' };
                        }

                        return { clicked: false, reason: 'no element from point', x, y };
                    }
                    """
                )

                print(f"动态点击弹窗 X 结果：{result}")
                time.sleep(1)
            except Exception as e:
                print(f"动态点击弹窗 X 失败：{e}")

            # 方案 3：按 ESC
            try:
                page.keyboard.press("Escape")
                print("已按 ESC")
                time.sleep(1)
            except Exception as e:
                print(f"ESC 失败：{e}")

            # 方案 4：强制移除弹窗层
            try:
                result = page.evaluate(
                    """
                    () => {
                        const keywords = [
                            'Do you love Godlike?',
                            'Switch to Premium today',
                            'Claim -50% Off',
                            "I'm fine with waiting in the queue"
                        ];

                        function isVisible(el) {
                            if (!el) return false;
                            const rect = el.getBoundingClientRect();
                            const style = window.getComputedStyle(el);
                            return (
                                rect.width > 0 &&
                                rect.height > 0 &&
                                style.display !== 'none' &&
                                style.visibility !== 'hidden'
                            );
                        }

                        const all = Array.from(document.querySelectorAll('body *'));
                        let removed = 0;

                        for (const el of all) {
                            const text = el.innerText || el.textContent || '';

                            if (isVisible(el) && keywords.some(k => text.includes(k))) {
                                let node = el;
                                let candidate = null;

                                for (let i = 0; i < 10 && node && node !== document.body; i++) {
                                    const rect = node.getBoundingClientRect();

                                    if (
                                        rect.width >= 250 &&
                                        rect.height >= 200 &&
                                        rect.width <= window.innerWidth * 0.95 &&
                                        rect.height <= window.innerHeight * 0.95
                                    ) {
                                        candidate = node;
                                    }

                                    node = node.parentElement;
                                }

                                if (candidate) {
                                    candidate.remove();
                                    removed++;
                                }
                            }
                        }

                        document.querySelectorAll(
                            '.v-overlay, .v-overlay__scrim, .modal-backdrop, [class*="overlay"], [class*="backdrop"], [role="dialog"]'
                        ).forEach(el => {
                            el.remove();
                            removed++;
                        });

                        document.body.style.overflow = 'auto';

                        return removed;
                    }
                    """
                )

                print(f"强制移除弹窗数量：{result}")
                time.sleep(1)
            except Exception as e:
                print(f"强制移除弹窗失败：{e}")

        def click_renew_button():
            """
            重点修复：
            不再使用 button:has-text("Renew").first。
            因为 first 可能找到隐藏的 Renew。
            这里会：
            1. 用 JS 找所有可见的 Renew
            2. 点击真正可见的 Renew
            3. 如果 JS 不行，再用 Playwright 遍历所有 Renew 文本
            """
            print("准备点击 Renew 按钮...")

            time.sleep(2)

            # 先尝试清理弹窗，但清不掉也没关系
            kill_advertising()

            # 方法 1：JS 找可见 Renew，然后点击
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

                        const all = Array.from(document.querySelectorAll('button, a, [role="button"], div, span'));

                        const matches = [];

                        for (const el of all) {
                            const text = (el.innerText || el.textContent || '').trim();

                            if (text === 'Renew') {
                                const clickable = findClickable(el);
                                const rect = clickable.getBoundingClientRect();

                                if (isVisible(clickable)) {
                                    matches.push({
                                        el: clickable,
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height,
                                        area: rect.width * rect.height,
                                        text: text
                                    });
                                }
                            }
                        }

                        if (matches.length === 0) {
                            return {
                                clicked: false,
                                reason: '没有找到可见的 Renew',
                                totalRenewText: all.filter(el => ((el.innerText || el.textContent || '').trim() === 'Renew')).length
                            };
                        }

                        // 优先点击面积比较小的按钮，避免点到整个大容器
                        matches.sort((a, b) => a.area - b.area);

                        const targetInfo = matches[0];
                        const target = targetInfo.el;

                        target.scrollIntoView({
                            block: 'center',
                            inline: 'center'
                        });

                        target.click();

                        return {
                            clicked: true,
                            x: targetInfo.x,
                            y: targetInfo.y,
                            width: targetInfo.width,
                            height: targetInfo.height,
                            matches: matches.length
                        };
                    }
                    """
                )

                print(f"JS 点击 Renew 结果：{result}")

                if result and result.get("clicked"):
                    time.sleep(3)
                    return True
            except Exception as e:
                print(f"JS 点击 Renew 失败：{e}")

            # 方法 2：Playwright 遍历所有 Renew 文本，找可见的点
            try:
                print("JS 没点到，尝试 Playwright 遍历 Renew 文本...")

                renew_texts = page.get_by_text("Renew", exact=True)
                count = renew_texts.count()

                print(f"页面中 Renew 文本数量：{count}")

                for i in range(count):
                    try:
                        item = renew_texts.nth(i)
                        box = item.bounding_box(timeout=2000)

                        if box:
                            x = box["x"] + box["width"] / 2
                            y = box["y"] + box["height"] / 2

                            print(f"尝试点击第 {i + 1} 个可见 Renew，坐标：{x}, {y}")

                            page.mouse.click(x, y)
                            time.sleep(3)

                            return True
                    except Exception as e:
                        print(f"第 {i + 1} 个 Renew 点击失败：{e}")

            except Exception as e:
                print(f"Playwright 遍历 Renew 失败：{e}")

            # 方法 3：根据你截图里的 Renew 区域，使用相对坐标兜底
            # 注意：这个坐标是最后兜底，前两个方法一般就够了
            try:
                print("前两种方法失败，使用固定坐标兜底点击 Renew...")

                page.mouse.click(185, 418)

                time.sleep(3)

                return True
            except Exception as e:
                print(f"固定坐标点击 Renew 失败：{e}")

            return False

        try:
            # 1. 登录
            print("正在登录...")

            page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)

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

            page.goto(SERVER_URL, wait_until="networkidle", timeout=60000)

            time.sleep(5)

            # 3. 保存一张进入页面后的截图，方便排查
            save_debug("after_server_page.png")

            # 4. 尝试关闭广告弹窗
            kill_advertising()

            # 5. 点击 Renew
            renew_clicked = click_renew_button()

            if not renew_clicked:
                print("没有成功点击 Renew，保存调试截图")
                save_debug("renew_click_failed.png")
                return

            print("已执行 Renew 点击，等待页面反应...")

            time.sleep(6)

            # Renew 之后可能再次弹窗，再清理一次
            kill_advertising()

            save_debug("after_renew_click.png")

            # 6. 尝试启动广告视频或者任务
            print("尝试启动视频播放...")

            try:
                page.mouse.click(640, 430)
                time.sleep(2)
            except Exception as e:
                print(f"点击视频区域失败：{e}")

            # 7. 监听领取按钮
            print("开始监听领取按钮...")

            found = False

            for i in range(45):
                try:
                    # 第一种找法：Get + hour
                    get_btn = page.locator('button:has-text("Get")').filter(has_text="hour").first

                    if get_btn.is_visible(timeout=1500):
                        print("【成功】检测到 Get hour 按钮，准备点击！")
                        get_btn.click(force=True)

                        time.sleep(5)

                        save_debug("success_final.png")

                        found = True
                        break
                except:
                    pass

                try:
                    # 第二种找法：所有可见 Get 按钮
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
                                    style.display !== 'none' &&
                                    style.visibility !== 'hidden' &&
                                    style.opacity !== '0'
                                );
                            }

                            const all = Array.from(document.querySelectorAll('button, a, [role="button"], div, span'));

                            for (const el of all) {
                                const text = (el.innerText || el.textContent || '').trim();

                                if (text.includes('Get') && isVisible(el)) {
                                    let node = el;

                                    for (let i = 0; i < 6 && node && node !== document.body; i++) {
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
                                            node.click();
                                            return true;
                                        }

                                        node = node.parentElement;
                                    }

                                    el.click();
                                    return true;
                                }
                            }

                            return false;
                        }
                        """
                    )

                    if result:
                        print("【成功】通过 JS 点击到了 Get 按钮")
                        time.sleep(5)

                        save_debug("success_final.png")

                        found = True
                        break
                except:
                    pass

                if i % 4 == 0:
                    kill_advertising()

                print(f"等待视频/领取按钮中... 第 {i + 1} 次检测")

                time.sleep(10)

            if not found:
                print("没有找到领取按钮，保存 final_debug.png")
                save_debug("final_debug.png")

        except Exception as e:
            print(f"异常：{e}")
            save_debug("error_exception.png")

        finally:
            browser.close()


if __name__ == "__main__":
    run()
