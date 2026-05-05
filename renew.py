import os
import time
from playwright.sync_api import sync_playwright


LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
            # 如果你想看浏览器操作过程，可以改成：
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

        def close_premium_popup():
            """
            关闭 50% Premium 弹窗。
            这次不再强制删除网页元素，只用点击。
            """
            print("尝试关闭 Premium 弹窗...")

            time.sleep(1)

            # 方法 1：点击截图里右上角 X 的准确位置
            # 你的截图中，弹窗 X 大约在 905,128
            try:
                page.mouse.click(905, 128)
                print("已点击弹窗右上角 X：905,128")
                time.sleep(1)
            except Exception as e:
                print(f"点击弹窗 X 失败：{e}")

            # 方法 2：点击底部 I'm fine...
            # 你的截图中，这个文字大约在 640,615
            try:
                page.mouse.click(640, 615)
                print("已点击底部关闭文字区域：640,615")
                time.sleep(1)
            except Exception as e:
                print(f"点击底部关闭文字失败：{e}")

            # 方法 3：按 ESC
            try:
                page.keyboard.press("Escape")
                print("已按 ESC")
                time.sleep(1)
            except Exception as e:
                print(f"ESC 失败：{e}")

        def click_overview_tab():
            """
            确保回到 Overview 页面。
            你之前后面跑到了 Tasks 页面，所以这里强制点回 Overview。
            """
            print("尝试回到 Overview 页面...")

            try:
                page.goto(SERVER_URL, wait_until="networkidle", timeout=60000)
                time.sleep(3)
                print("已重新打开服务器 Overview 地址")
            except Exception as e:
                print(f"重新打开服务器页面失败：{e}")

            close_premium_popup()

            # 额外点一下上方 Overview 标签。
            # 这个坐标来自你的截图，上方蓝色 Overview 标签大约在 190,165。
            try:
                page.mouse.click(190, 165)
                print("已点击上方 Overview 标签")
                time.sleep(2)
            except Exception as e:
                print(f"点击 Overview 标签失败：{e}")

            close_premium_popup()

        def click_renew_button():
            """
            点击 Renew 按钮。
            这次重点改动：
            1. 不再依赖 button:has-text("Renew")。
            2. 优先根据 Renew Server 卡片定位。
            3. 定位不到时，用多个坐标兜底。
            """
            print("准备点击 Renew 按钮...")

            close_premium_popup()

            save_debug("before_click_renew.png")

            # 方法 1：根据 Renew Server 文字定位卡片，再点卡片里的按钮
            try:
                renew_server_text = page.get_by_text("Renew Server", exact=True)

                if renew_server_text.is_visible(timeout=5000):
                    box = renew_server_text.bounding_box(timeout=5000)

                    if box:
                        print(f"找到 Renew Server 标题，位置：{box}")

                        # Renew 按钮通常在 Renew Server 标题下方约 55 像素，偏左一点
                        x = box["x"] + 30
                        y = box["y"] + 58

                        print(f"尝试根据 Renew Server 标题点击 Renew：x={x}, y={y}")
                        page.mouse.click(x, y)

                        time.sleep(4)
                        save_debug("after_click_renew_by_title.png")
                        return True
            except Exception as e:
                print(f"根据 Renew Server 标题点击失败：{e}")

            # 方法 2：根据提示文字定位卡片
            try:
                free_server_text = page.get_by_text("Your free server will be suspended")

                if free_server_text.is_visible(timeout=5000):
                    box = free_server_text.bounding_box(timeout=5000)

                    if box:
                        print(f"找到 suspended 提示文字，位置：{box}")

                        # Renew 按钮通常在这行提示下方约 32 像素，靠左
                        x = box["x"] + 25
                        y = box["y"] + 34

                        print(f"尝试根据 suspended 提示点击 Renew：x={x}, y={y}")
                        page.mouse.click(x, y)

                        time.sleep(4)
                        save_debug("after_click_renew_by_suspended_text.png")
                        return True
            except Exception as e:
                print(f"根据 suspended 提示点击失败：{e}")

            # 方法 3：尝试通过 JS 找包含 Renew Server 的区域，然后点击里面的按钮
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

                        const all = Array.from(document.querySelectorAll('body *'));

                        let titleEl = null;

                        for (const el of all) {
                            const text = (el.innerText || el.textContent || '').trim();

                            if (text === 'Renew Server' && isVisible(el)) {
                                titleEl = el;
                                break;
                            }
                        }

                        if (!titleEl) {
                            return {
                                clicked: false,
                                reason: '找不到 Renew Server'
                            };
                        }

                        let card = titleEl;

                        for (let i = 0; i < 8 && card && card !== document.body; i++) {
                            const rect = card.getBoundingClientRect();

                            if (
                                rect.width > 150 &&
                                rect.height > 80 &&
                                rect.width < 500 &&
                                rect.height < 300
                            ) {
                                break;
                            }

                            card = card.parentElement;
                        }

                        if (!card || card === document.body) {
                            return {
                                clicked: false,
                                reason: '找不到 Renew Server 卡片'
                            };
                        }

                        const buttons = Array.from(card.querySelectorAll('button, a, [role="button"], div, span'));

                        for (const btn of buttons) {
                            const text = (btn.innerText || btn.textContent || '').trim();
                            const rect = btn.getBoundingClientRect();

                            if (
                                isVisible(btn) &&
                                (
                                    text === 'Renew' ||
                                    text.includes('Renew') ||
                                    rect.width >= 30 && rect.width <= 120 && rect.height >= 20 && rect.height <= 60
                                )
                            ) {
                                btn.click();

                                return {
                                    clicked: true,
                                    method: 'card button',
                                    text: text,
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                };
                            }
                        }

                        const cardRect = card.getBoundingClientRect();

                        const x = cardRect.x + 35;
                        const y = cardRect.y + cardRect.height - 30;

                        const target = document.elementFromPoint(x, y);

                        if (target) {
                            target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
                            target.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
                            target.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y }));

                            return {
                                clicked: true,
                                method: 'card coordinate',
                                x: x,
                                y: y,
                                targetText: target.innerText || target.textContent || ''
                            };
                        }

                        return {
                            clicked: false,
                            reason: '卡片内没有可点击目标'
                        };
                    }
                    """
                )

                print(f"JS 点击 Renew 结果：{result}")

                if result and result.get("clicked"):
                    time.sleep(4)
                    save_debug("after_click_renew_by_js_card.png")
                    return True

            except Exception as e:
                print(f"JS 卡片点击 Renew 失败：{e}")

            # 方法 4：坐标兜底
            # 注意：这次不使用之前那个容易点到左侧 Tasks 的坐标。
            # 从你的 after_server_page 截图看，Renew 按钮在左侧内容区，真实坐标更接近 188,415。
            # 但为了避免点到左侧菜单，这里会先确保 Overview 页，然后尝试多个附近坐标。
            fallback_points = [
                (188, 415),
                (190, 420),
                (200, 418),
                (180, 417),
                (185, 405),
            ]

            for x, y in fallback_points:
                try:
                    print(f"尝试固定坐标点击 Renew：x={x}, y={y}")
                    page.mouse.click(x, y)
                    time.sleep(4)

                    save_debug(f"after_click_renew_fixed_{x}_{y}.png")

                    # 点完后返回 True，让后续继续执行
                    return True
                except Exception as e:
                    print(f"固定坐标 {x},{y} 点击失败：{e}")

            return False

        def click_possible_video_or_ad():
            """
            Renew 后尝试点击广告/视频区域。
            """
            print("尝试启动视频或广告任务...")

            close_premium_popup()

            possible_points = [
                (640, 430),
                (650, 360),
                (700, 420),
                (500, 430),
                (640, 500),
            ]

            for x, y in possible_points:
                try:
                    print(f"尝试点击视频/广告区域：x={x}, y={y}")
                    page.mouse.click(x, y)
                    time.sleep(2)
                except Exception as e:
                    print(f"点击视频/广告区域失败：{e}")

        def click_get_button_if_exists():
            """
            尝试点击 Get / Claim / Collect 一类的领取按钮。
            """
            # 方法 1：Playwright 找按钮文字
            possible_texts = [
                "Get",
                "Claim",
                "Collect",
                "Get reward",
                "Get Reward",
                "Claim reward",
                "Claim Reward"
            ]

            for text in possible_texts:
                try:
                    loc = page.get_by_text(text, exact=False)
                    count = loc.count()

                    for i in range(count):
                        item = loc.nth(i)

                        try:
                            if item.is_visible(timeout=1000):
                                box = item.bounding_box(timeout=1000)

                                if box:
                                    x = box["x"] + box["width"] / 2
                                    y = box["y"] + box["height"] / 2

                                    print(f"检测到领取相关文字 {text}，点击：x={x}, y={y}")
                                    page.mouse.click(x, y)

                                    time.sleep(5)
                                    return True
                        except:
                            pass
                except:
                    pass

            # 方法 2：JS 查找可见按钮
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

                        const keywords = ['Get', 'Claim', 'Collect', 'Reward', 'hour'];

                        const all = Array.from(document.querySelectorAll('button, a, [role="button"], div, span'));

                        for (const el of all) {
                            const text = (el.innerText || el.textContent || '').trim();

                            if (isVisible(el) && keywords.some(k => text.includes(k))) {
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

                                        const rect = node.getBoundingClientRect();

                                        return {
                                            clicked: true,
                                            text: text,
                                            x: rect.x,
                                            y: rect.y,
                                            width: rect.width,
                                            height: rect.height
                                        };
                                    }

                                    node = node.parentElement;
                                }

                                el.click();

                                const rect = el.getBoundingClientRect();

                                return {
                                    clicked: true,
                                    text: text,
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                };
                            }
                        }

                        return {
                            clicked: false,
                            reason: '没有找到领取按钮'
                        };
                    }
                    """
                )

                print(f"JS 查找领取按钮结果：{result}")

                if result and result.get("clicked"):
                    time.sleep(5)
                    return True

            except Exception as e:
                print(f"JS 查找领取按钮失败：{e}")

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
                print("没有看到 Through Login/Password，继续尝试登录")

            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])

            page.locator('button:has-text("Login")').first.click()

            page.wait_for_url(lambda url: "login" not in url, timeout=25000)

            print("登录成功！")

            # 2. 打开服务器页面
            print("前往管理页...")

            page.goto(SERVER_URL, wait_until="networkidle", timeout=60000)

            time.sleep(5)

            save_debug("after_server_page.png")

            # 3. 关闭弹窗
            close_premium_popup()

            # 4. 确保回到 Overview
            click_overview_tab()

            save_debug("after_back_to_overview.png")

            # 5. 点击 Renew
            renew_clicked = click_renew_button()

            if not renew_clicked:
                print("Renew 没有点击成功，保存截图 renew_click_failed.png")
                save_debug("renew_click_failed.png")
                return

            print("已尝试点击 Renew，等待页面反应...")

            time.sleep(6)

            close_premium_popup()

            save_debug("after_renew_click.png")

            # 6. 尝试启动视频/广告
            click_possible_video_or_ad()

            save_debug("after_try_video_click.png")

            # 7. 等待并尝试点击领取按钮
            print("开始监听领取按钮...")

            found = False

            for i in range(45):
                close_premium_popup()

                if click_get_button_if_exists():
                    print("【成功】检测到并点击了领取按钮")
                    save_debug("success_final.png")
                    found = True
                    break

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
