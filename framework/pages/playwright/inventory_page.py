from framework.pages.playwright.base_page import BasePage
from framework.utils import price_to_float


class InventoryPage(BasePage):
    def title(self) -> str:
        return self.text("title")

    def product_names(self) -> list[str]:
        return self.texts(".inventory-item .item-name")

    def product_prices(self) -> list[float]:
        return [price_to_float(t) for t in self.texts(".inventory-item .item-price")]

    def sort_by(self, value: str) -> None:
        self.loc("sort").select_option(value)
        self.page.wait_for_url(lambda url: f"sort={value}" in url)

    def add_to_cart(self, product_id: int) -> None:
        self.click(f"add-to-cart-{product_id}")

    def remove_from_cart(self, product_id: int) -> None:
        self.click(f"remove-{product_id}")

    def is_add_enabled(self, product_id: int) -> bool:
        return self.loc(f"add-to-cart-{product_id}").is_enabled()

    def badge_count(self) -> int:
        return int(self.text("cart-badge")) if self.exists("cart-badge") else 0

    def open_cart(self) -> None:
        self.click("cart-link")

    def logout(self) -> None:
        self.click("logout")
