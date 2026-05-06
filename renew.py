import os
import time
import requests
from playwright.sync_api import sync_playwright

# ==========================
# 配置（和别人完全一样）
# ==========================
LOGIN_URL = "https://ultra.panel.godlike.host/login"
SERVER_URL = "https://ultra.panel.godlike.host/server/2a3af930"

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

def send_tg(msg):
    if TG_BOT_TOKEN and TG_CHAT_ID:
        try:
            requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", json={
                "chat_id": TG_CHAT_ID,
                "text": f"【Godlike 续期】\n{msg}"
            }, timeout=10)
        except:
            pass

def run():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            ctx = browser.new_context(viewport={"width": 1280, "height": 800})
            page = ctx.new_page()

            # 登录
            page.goto(LOGIN_URL)
            page.wait_for_selector('input[type="email"]', timeout=30000)
            page.fill('input[type="email"]', os.environ["GODLIKE_EMAIL"])
            page.fill('input[type="password"]', os.environ["GODLIKE_PASSWORD"])
            page.click('button:has-text("Login")')
            page.wait_for_url(lambda u: "login" not in u, timeout=30000)

            # 进入服务器
            page.goto(SERVER_URL)
            page.wait_for_selector('button:has-text("Renew")', timeout=30000)

            # 点击 Renew
            page.click('button:has-text("Renew")')
            time.sleep(3)

            # 点击 24h
            page.evaluate('''() => {
                const list = document.querySelectorAll("div");
                for(let i=0;i<list.length;i++){
                    if(list[i].innerText.includes("24 hours")){
                        list[i].click();
                        break;
                    }
                }
            }''')
            time.sleep(3)

            # 确认
            page.evaluate('''() => {
                const btns = document.querySelectorAll("button");
                for(let i=0;i<btns.length;i++){
                    if(btns[i].innerText.includes("Confirm")||btns[i].innerText.includes("Renew")){
                        btns[i].click();
                        break;
                    }
                }
            }''')
            time.sleep(5)

            print("✅ 续期成功")
            send_tg("✅ 续期 24 小时成功！")

    except Exception as e:
        err = f"❌ 失败：{str(e)[:100]}"
        print(err)
        send_tg(err)
        raise
    finally:
        if 'browser' in locals():
            browser.close()

if __name__ == "__main__":
    run()
