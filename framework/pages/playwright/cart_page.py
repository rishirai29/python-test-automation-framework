from framework.pages.playwright.base_page import BasePage
from framework.utils import price_to_float


class CartPage(BasePage):
    def item_names(self) -> list[str]:
        return self.texts(".cart-item .item-name")

    def total(self) -> float:
        return price_to_float(self.text("cart-total"))

    def remove(self, product_id: int) -> None:
        self.click(f"remove-{product_id}")

    def is_checkout_enabled(self) -> bool:
        return self.loc("checkout").is_enabled()

    def checkout(self) -> None:
        self.click("checkout")

    def confirmation_header(self) -> str:
        return self.text("complete-header")

    def order_id(self) -> int:
        return int(self.text("order-id"))
