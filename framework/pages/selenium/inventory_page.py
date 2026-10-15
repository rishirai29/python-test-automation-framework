from selenium.webdriver.support.ui import Select

from framework.pages.selenium.base_page import BasePage
from framework.utils import price_to_float


class InventoryPage(BasePage):
    def title(self) -> str:
        return self.text("title")

    def product_names(self) -> list[str]:
        return self.texts(".inventory-item .item-name")

    def product_prices(self) -> list[float]:
        return [price_to_float(t) for t in self.texts(".inventory-item .item-price")]

    def sort_by(self, value: str) -> None:
        old_page = self._page_marker()
        self._retry(lambda: Select(self.element("sort")).select_by_value(value))
        self.wait.until(lambda d: f"sort={value}" in d.current_url)
        self.wait_for_navigation(old_page)

    def add_to_cart(self, product_id: int) -> None:
        self.click(f"add-to-cart-{product_id}")

    def remove_from_cart(self, product_id: int) -> None:
        self.click(f"remove-{product_id}")

    def is_add_enabled(self, product_id: int) -> bool:
        return self._retry(lambda: self.element(f"add-to-cart-{product_id}").is_enabled())

    def badge_count(self) -> int:
        return int(self.text("cart-badge")) if self.exists("cart-badge") else 0

    def open_cart(self) -> None:
        self.click("cart-link")

    def logout(self) -> None:
        self.click("logout")
