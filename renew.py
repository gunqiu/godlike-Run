import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
            # 如果想看浏览器操作，把上面改成 headless=False
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

        def safe_goto(url, name="页面"):
            """
            重要修复：
            不再使用 networkidle，因为这个网站会一直有后台请求，容易超时。
            """
            print(f"正在打开{name}：{url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(5)
                print(f"{name}已打开")
                return True
            except PlaywrightTimeoutError:
                print(f"{name}打开超时，但继续执行，因为页面可能已经加载出来")
                time.sleep(5)
                return True
            except Exception as e:
                print(f"{name}打开异常：{e}")
                time.sleep(5)
                return False

        def close_premium_popup():
            """
            关闭中间的 50% Premium 弹窗。
            注意：这版不强制删除网页元素，避免把正常页面删坏。
            """
            print("尝试关闭 Premium 弹窗...")

            time.sleep(1)

            # 先尝试点右上角 X
            # 根据你的截图，X 大约在 905,128
            try:
                page.mouse.click(905, 128)
                print("已尝试点击 Premium 弹窗 X")
                time.sleep(1)
            except Exception as e:
                print(f"点击 Premium X 失败：{e}")

            # 再尝试点底部 I'm fine...
            # 根据你的截图，文字大约在 640,615
            try:
                page.mouse.click(640, 615)
                print("已尝试点击 I'm fine 文字")
                time.sleep(1)
            except Exception as e:
                print(f"点击 I'm fine 失败：{e}")

            # 再按 ESC
            try:
                page.keyboard.press("Escape")
                print("已按 ESC")
                time.sleep(1)
            except Exception as e:
                print(f"ESC 失败：{e}")

        def close_survey_popup():
            """
            关闭左下角问卷弹窗。
            你 final_debug.png 里面左下角出现了 recommend us 小问卷。
            """
            print("尝试关闭左下角问卷弹窗...")

            # 根据截图，问卷右上角 X 大概在 x=210, y=375 附近
            points = [
                (210, 375),
                (205, 370),
                (215, 380),
            ]

            for x, y in points:
                try:
                    page.mouse.click(x, y)
                    print(f"已尝试点击问卷关闭按钮：{x},{y}")
                    time.sleep(0.5)
                except:
                    pass

        def click_overview():
            """
            确保在 Overview 页面。
            """
            print("尝试回到 Overview 页面...")

            # 左侧 Overview 菜单坐标
            try:
                page.mouse.click(70, 145)
                time.sleep(2)
            except:
                pass

            # 上方 Overview 标签坐标
            try:
                page.mouse.click(195, 165)
                time.sleep(2)
            except:
                pass

            close_premium_popup()
            close_survey_popup()

        def click_renew_button():
            """
            重点修复：点击 Renew 按钮。
            根据你的截图，真正按钮中心大约在 190,435。
            之前点 188,415 偏上，可能点到了 FREE 标签附近。
            """
            print("准备点击 Renew 按钮...")

            close_premium_popup()
            close_survey_popup()

            save_debug("before_click_renew.png")

            # 方法 1：直接用最准确的截图坐标
            # 从你最新截图看，Renew 按钮中心大约是 x=190, y=435
            fixed_points = [
                (190, 435),
                (195, 435),
                (185, 435),
                (190, 430),
                (200, 435),
                (190, 440),
            ]

            for x, y in fixed_points:
                try:
                    print(f"尝试固定坐标点击 Renew：x={x}, y={y}")
                    page.mouse.move(x, y)
                    time.sleep(0.3)
                    page.mouse.down()
                    time.sleep(0.2)
                    page.mouse.up()
                    time.sleep(4)

                    save_debug(f"after_click_renew_fixed_{x}_{y}.png")

                    # 点击后尝试处理可能弹出的广告/弹窗
                    close_premium_popup()
                    close_survey_popup()

                    return True
                except Exception as e:
                    print(f"固定坐标点击 Renew 失败：{x},{y}，错误：{e}")

            # 方法 2：用 JS 在这个坐标上触发点击
            try:
                result = page.evaluate(
                    """
                    () => {
                        const points = [
                            [190, 435],
                            [195, 435],
                            [185, 435],
                            [190, 430],
                            [200, 435],
                            [190, 440]
                        ];

                        for (const [x, y] of points) {
                            const el = document.elementFromPoint(x, y);

                            if (el) {
                                el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: x, clientY: y }));
                                el.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: x, clientY: y }));
                                el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
                                el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
                                el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y }));

                                return {
                                    clicked: true,
                                    x,
                                    y,
                                    tag: el.tagName,
                                    text: el.innerText || el.textContent || '',
                                    className: String(el.className || '')
                                };
                            }
                        }

                        return {
                            clicked: false,
                            reason: '坐标上没有元素'
                        };
                    }
                    """
                )

                print(f"JS 坐标点击 Renew 结果：{result}")
                time.sleep(4)
                save_debug("after_click_renew_by_js_point.png")

                if result and result.get("clicked"):
                    return True

            except Exception as e:
                print(f"JS 坐标点击 Renew 失败：{e}")

            # 方法 3：根据 Renew Server 卡片文字定位
            try:
                print("尝试根据 Renew Server 文字定位按钮...")

                renew_title = page.get_by_text("Renew Server", exact=True)

                if renew_title.is_visible(timeout=3000):
                    box = renew_title.bounding_box(timeout=3000)

                    if box:
                        print(f"找到 Renew Server 标题：{box}")

                        # 根据截图：标题下方约 52-62 像素处是按钮中心
                        x = box["x"] + 30
                        y = box["y"] + 60

                        print(f"根据标题点击 Renew：x={x}, y={y}")
                        page.mouse.click(x, y)

                        time.sleep(4)
                        save_debug("after_click_renew_by_title.png")
                        return True

            except Exception as e:
                print(f"根据 Renew Server 定位失败：{e}")

            print("Renew 按钮点击失败")
            return False

        def click_possible_confirm_or_watch_button():
            """
            点击 Renew 后，可能会出现确认按钮、Watch Ad、Start、Claim 之类按钮。
            这个函数尝试找这些按钮。
            """
            print("尝试寻找 Renew 后出现的确认/广告按钮...")

            close_premium_popup()
            close_survey_popup()

            possible_words = [
                "Watch",
                "watch",
                "Ad",
                "ad",
                "Start",
                "start",
                "Continue",
                "continue",
                "Confirm",
                "confirm",
                "Renew",
                "renew",
                "Claim",
                "claim",
                "Get",
                "get"
            ]

            for word in possible_words:
                try:
                    loc = page.get_by_text(word, exact=False)
                    count = loc.count()

                    for i in range(count):
                        item = loc.nth(i)

                        try:
                            if item.is_visible(timeout=1000):
                                box = item.bounding_box(timeout=1000)

                                if box:
                                    x = box["x"] + box["width"] / 2
                                    y = box["y"] + box["height"] / 2

                                    # 避免点击 Upgrade Plan 和 Boost My Server
                                    if y < 170:
                                        continue

                                    print(f"发现可能按钮文字：{word}，点击坐标：x={x}, y={y}")
                                    page.mouse.click(x, y)
                                    time.sleep(4)
                                    save_debug(f"after_click_possible_{word}_{i}.png")
                                    return True
                        except:
                            pass

                except:
                    pass

            # 兜底：点击右侧中间区域，可能是广告区域
            possible_points = [
                (640, 430),
                (650, 400),
                (700, 430),
                (600, 430),
                (640, 500),
            ]

            for x, y in possible_points:
                try:
                    print(f"尝试点击可能的视频/广告区域：{x},{y}")
                    page.mouse.click(x, y)
                    time.sleep(3)
                except:
                    pass

            return False

        def click_get_button_if_exists():
            """
            检查是否出现领取按钮。
            """
            print("检查是否出现领取按钮...")

            close_premium_popup()
            close_survey_popup()

            possible_texts = [
                "Get",
                "Claim",
                "Collect",
                "Reward",
                "hour",
                "hours"
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

                                    # 避免点到无关顶部区域
                                    if y < 170:
                                        continue

                                    print(f"检测到领取相关文字：{text}，点击：x={x}, y={y}")
                                    page.mouse.click(x, y)
                                    time.sleep(5)
                                    return True
                        except:
                            pass

                except:
                    pass

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
                print("没有看到 Through Login/Password，继续尝试登录")

            page.locator('input[type="email"]').first.fill(os.environ["GODLIKE_EMAIL"])
            page.locator('input[type="password"]').first.fill(os.environ["GODLIKE_PASSWORD"])

            page.locator('button:has-text("Login")').first.click()

            page.wait_for_url(lambda url: "login" not in url, timeout=25000)

            print("登录成功！")

            # 2. 打开服务器页
            print("前往管理页...")

            safe_goto(SERVER_URL, "服务器管理页")

            save_debug("after_server_page.png")

            # 3. 回到 Overview
            click_overview()

            save_debug("after_back_to_overview.png")

            # 4. 点击 Renew
            renew_clicked = click_renew_button()

            if not renew_clicked:
                print("Renew 没有点击成功，保存 renew_click_failed.png")
                save_debug("renew_click_failed.png")
                return

            print("已尝试点击 Renew，等待页面反应...")

            time.sleep(6)

            close_premium_popup()
            close_survey_popup()

            save_debug("after_renew_click.png")

            # 5. 点击可能出现的确认/广告按钮
            click_possible_confirm_or_watch_button()

            save_debug("after_try_confirm_or_watch.png")

            # 6. 等待并点击领取按钮
            print("开始监听领取按钮...")

            found = False

            for i in range(45):
                if click_get_button_if_exists():
                    print("【成功】检测到并点击领取按钮")
                    save_debug("success_final.png")
                    found = True
                    break

                # 每几轮再尝试点一下可能的确认/广告区域
                if i % 5 == 0:
                    click_possible_confirm_or_watch_button()

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
