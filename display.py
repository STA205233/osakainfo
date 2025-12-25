from playwright.sync_api import sync_playwright
import sys
import os
import time

def make_screenshot(output="grafana.png"):
    GRAFANA_URL = sys.argv[1]
    USER = os.getenv("GRAFANA_USER")
    PASSWORD = os.getenv("GRAFANA_PASSWD")
    print("loading:", GRAFANA_URL)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 4000})

        page.goto(GRAFANA_URL)  # 読み込み待ち
        page.wait_for_timeout(2000)                       # パネル描画の「余韻」待ち（必要なことが多い）
        page.fill('input[name="user"]', USER)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')
        page.click("button[id=dock-menu-button]")
        time.sleep(5)                       # ログイン処理待ち
        page.screenshot(path=output, full_page=True)
        browser.close()