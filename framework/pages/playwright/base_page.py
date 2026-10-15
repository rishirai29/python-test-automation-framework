"""Base page object for Playwright (sync API) using data-test locators."""
from playwright.sync_api import Locator, Page


class BasePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def loc(self, name: str) -> Locator:
        return self.page.locator(f'[data-test="{name}"]')

    def open(self, path: str = "") -> None:
        self.page.goto(f"{self.base_url}{path}")

    def current_url(self) -> str:
        return self.page.url

    def click(self, name: str) -> None:
        self.loc(name).click()
        self.page.wait_for_load_state()

    def type(self, name: str, text: str) -> None:
        self.loc(name).fill(text)

    def text(self, name: str) -> str:
        return self.loc(name).inner_text().strip()

    def exists(self, name: str) -> bool:
        return self.loc(name).count() > 0

    def texts(self, css: str) -> list[str]:
        return [t.strip() for t in self.page.locator(css).all_inner_texts()]
