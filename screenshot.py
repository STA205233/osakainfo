from playwright.sync_api import sync_playwright
import os
import time


def make_screenshot(output="grafana.png", url=None, password=None, user=None):
    GRAFANA_URL = url or os.getenv("GRAFANA_URL")
    USER = user or os.getenv("GRAFANA_USER")
    PASSWORD = password or os.getenv("GRAFANA_PASSWD")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 3000})

        page.goto(GRAFANA_URL)
        page.wait_for_timeout(2000)
        page.fill('input[name="user"]', USER)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')
        page.click("button[id=dock-menu-button]")
        time.sleep(5)
        page.screenshot(path=output, full_page=True)
        browser.close()
