import os
import time
from playwright.sync_api import sync_playwright


SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"
LOGIN_URL = "https://ultra.panel.godlike.host/login"


def run():
    with sync_playwright() as p:
        # 如果你想看浏览器实际操作过程，把 headless=True 改成 headless=False
        browser = p.chromium.launch(
            headless=True,
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

        def kill_advertising():
            """
            强力关闭 Godlike 50% Off 弹窗。
            顺序：
            1. 点击 I'm fine with waiting in the queue
            2. 根据弹窗文字找到弹窗，然后点右上角 X
            3. 按 ESC
            4. 使用截图中的固定坐标点击 X
            5. JS 强制删除弹窗和遮罩
            """
            print("正在清理广告弹窗...")

            time.sleep(1)

            # 方案 1：点击底部文字关闭
            try:
                fine_text = "I'm fine with waiting in the queue"
                fine_btn = page.get_by_text(fine_text, exact=True)

                if fine_btn.is_visible(timeout=1500):
                    fine_btn.click(force=True)
                    print("已点击：I'm fine with waiting in the queue")
                    time.sleep(1)
                    return
            except Exception as e:
                print(f"点击底部关闭文字失败：{e}")

            # 方案 2：根据弹窗标题定位，然后点击右上角 X
            try:
                modal_title = page.get_by_text("Do you love Godlike?", exact=True)

                if modal_title.is_visible(timeout=1500):
                    print("检测到 Godlike 弹窗，准备点击右上角 X")

                    # 尝试找到包含弹窗标题的较大父元素
                    modal_box_locator = page.locator("text=Do you love Godlike?").locator(
                        "xpath=ancestor::*["
                        "contains(@class, 'v-card') "
                        "or contains(@class, 'modal') "
                        "or contains(@class, 'dialog') "
                        "or contains(@class, 'overlay')"
                        "][1]"
                    )

                    box = None

                    try:
                        box = modal_box_locator.bounding_box(timeout=2000)
                    except:
                        box = None

                    if box:
                        # 点击弹窗右上角 X 附近
                        x = box["x"] + box["width"] - 30
                        y = box["y"] + 30

                        page.mouse.click(x, y)
                        print(f"已点击弹窗右上角 X：x={x}, y={y}")
                        time.sleep(1)
                        return
                    else:
                        print("没有获取到弹窗边界，准备使用固定坐标")
            except Exception as e:
                print(f"通过弹窗标题关闭失败：{e}")

            # 方案 3：按 ESC
            try:
                page.keyboard.press("Escape")
                print("已按 ESC")
                time.sleep(1)
            except Exception as e:
                print(f"ESC 关闭失败：{e}")

            # 方案 4：根据你截图中的 1280x800 画面，X 大约在 905,128
            try:
                page.mouse.click(905, 128)
                print("已使用固定坐标点击右上角 X：905,128")
                time.sleep(1)
            except Exception as e:
                print(f"固定坐标点击 X 失败：{e}")

            # 方案 5：尝试点击底部关闭文字的大概位置，截图里大约在 y=615
            try:
                page.mouse.click(640, 615)
                print("已使用固定坐标点击底部关闭文字：640,615")
                time.sleep(1)
            except Exception as e:
                print(f"固定坐标点击底部文字失败：{e}")

            # 方案 6：最后兜底，JS 强制删除弹窗和遮罩
            try:
                page.evaluate(
                    """
                    () => {
                        const keywords = [
                            'Do you love Godlike?',
                            'Switch to Premium today',
                            'Claim -50% Off',
                            "I'm fine with waiting in the queue"
                        ];

                        const all = Array.from(document.querySelectorAll('body *'));

                        for (const el of all) {
                            const text = el.innerText || '';

                            if (keywords.some(k => text.includes(k))) {
                                let node = el;

                                for (let i = 0; i < 8 && node && node !== document.body; i++) {
                                    const style = window.getComputedStyle(node);
                                    const rect = node.getBoundingClientRect();
                                    const className = String(node.className || '');

                                    const looksLikeModal =
                                        rect.width > 300 &&
                                        rect.height > 200 &&
                                        (
                                            style.position === 'fixed' ||
                                            style.position === 'absolute' ||
                                            node.getAttribute('role') === 'dialog' ||
                                            className.includes('modal') ||
                                            className.includes('dialog') ||
                                            className.includes('overlay') ||
                                            className.includes('v-card')
                                        );

                                    if (looksLikeModal) {
                                        node.remove();
                                        break;
                                    }

                                    node = node.parentElement;
                                }
                            }
                        }

                        document.querySelectorAll(
                            '.v-overlay, .v-overlay__scrim, .modal-backdrop, [class*="overlay"], [class*="backdrop"], [role="dialog"]'
                        ).forEach(el => el.remove());

                        document.body.style.overflow = 'auto';
                    }
                    """
                )

                print("已执行 JS 强制清理弹窗")
                time.sleep(1)
            except Exception as e:
                print(f"JS 强制清理失败：{e}")

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

            page.wait_for_url(lambda url: "login" not in url, timeout=20000)

            print("登录成功！")

            # 2. 前往服务器管理页
            print("前往管理页...")
            page.goto(SERVER_URL, wait_until="networkidle", timeout=60000)

            # 3. 等待广告弹窗出现
            print("等待广告弹窗...")

            try:
                page.get_by_text("Do you love Godlike?", exact=True).wait_for(timeout=12000)
                print("检测到广告弹窗")
            except:
                print("没有检测到广告弹窗，继续执行")

            # 4. 清理弹窗
            kill_advertising()

            # 5. 点击 Renew 按钮
            print("准备点击 Renew 按钮...")

            renew_btn = page.locator('button:has-text("Renew")').first
            renew_btn.scroll_into_view_if_needed(timeout=10000)

            time.sleep(1)

            renew_btn.click(force=True)
            print("已点击 Renew")

            time.sleep(5)

            # Renew 后可能再次出现广告弹窗
            kill_advertising()

            # 6. 启动视频播放
            print("启动视频播放...")

            # 点击页面中间区域，尝试播放广告视频
            page.mouse.click(640, 430)

            time.sleep(2)

            # 7. 开始监听领取按钮
            print("开始监听领取按钮...")

            found = False

            for i in range(45):
                try:
                    # 尝试找包含 Get 和 hour 的按钮
                    get_btn = page.locator('button:has-text("Get")').filter(has_text="hour").first

                    if get_btn.is_visible(timeout=1500):
                        print("【成功】检测到领取按钮，准备点击！")
                        get_btn.click(force=True)

                        time.sleep(5)

                        page.screenshot(path="success_final.png", full_page=True)
                        print("已截图保存：success_final.png")

                        found = True
                        break
                except:
                    pass

                # 每隔一段时间清理一次弹窗
                if i % 4 == 0:
                    kill_advertising()

                print(f"等待视频中... 第 {i + 1} 次检测")
                time.sleep(10)

            if not found:
                print("没有找到领取按钮，保存调试截图 final_debug.png")
                page.screenshot(path="final_debug.png", full_page=True)

        except Exception as e:
            print(f"异常：{e}")

            try:
                page.screenshot(path="error_exception.png", full_page=True)
                print("已截图保存：error_exception.png")
            except:
                print("异常截图保存失败")

        finally:
            browser.close()


if __name__ == "__main__":
    run()
