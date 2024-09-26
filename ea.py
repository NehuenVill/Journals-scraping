import re
from playwright.sync_api import Page, expect
import time


def test_get_started_link(page: Page):

    page.goto("https://www.wsj.com/news/markets/oil-gold-commodities-futures")

    time.sleep(600)

    element_text = page.text_content("h3")

    print(element_text)


