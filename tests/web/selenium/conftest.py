import pytest

from framework import config
from framework.pages.selenium.cart_page import CartPage
from framework.pages.selenium.inventory_page import InventoryPage
from framework.pages.selenium.login_page import LoginPage


@pytest.fixture
def login_page(driver, base_url):
    return LoginPage(driver, base_url)


@pytest.fixture
def inventory_page(driver, base_url):
    return InventoryPage(driver, base_url)


@pytest.fixture
def cart_page(driver, base_url):
    return CartPage(driver, base_url)


@pytest.fixture
def logged_in(login_page, inventory_page):
    """Log in through the UI and return the inventory page."""
    login_page.open_login()
    login_page.login(*config.VALID_USER)
    assert inventory_page.title() == "Products"
    return inventory_page
