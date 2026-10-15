import pytest

from framework import config
from framework.pages.playwright.cart_page import CartPage
from framework.pages.playwright.inventory_page import InventoryPage
from framework.pages.playwright.login_page import LoginPage


@pytest.fixture
def login_page(pw_page, base_url):
    return LoginPage(pw_page, base_url)


@pytest.fixture
def inventory_page(pw_page, base_url):
    return InventoryPage(pw_page, base_url)


@pytest.fixture
def cart_page(pw_page, base_url):
    return CartPage(pw_page, base_url)


@pytest.fixture
def logged_in(login_page, inventory_page):
    login_page.open_login()
    login_page.login(*config.VALID_USER)
    assert inventory_page.title() == "Products"
    return inventory_page
