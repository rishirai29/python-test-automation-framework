import pytest

from framework import config
from framework.utils import load_json

pytestmark = [pytest.mark.web, pytest.mark.playwright]

LOGIN_CASES = load_json("login_cases.json")


@pytest.mark.smoke
def test_valid_login_lands_on_products_page(login_page, inventory_page):
    login_page.open_login()
    login_page.login(*config.VALID_USER)
    assert inventory_page.title() == "Products"
    assert "/inventory" in login_page.current_url()


@pytest.mark.regression
@pytest.mark.parametrize("case", LOGIN_CASES, ids=[c["id"] for c in LOGIN_CASES])
def test_invalid_login_shows_error(login_page, case):
    login_page.open_login()
    login_page.login(case["username"], case["password"])
    assert login_page.error_message() == case["error"]
    assert login_page.current_url().endswith("/login")


@pytest.mark.regression
def test_logout_returns_to_login_page(logged_in, login_page):
    logged_in.logout()
    assert login_page.current_url().endswith("/login")


@pytest.mark.regression
def test_protected_page_redirects_to_login(login_page):
    login_page.open("/inventory")
    assert login_page.current_url().endswith("/login")
    assert "logged in" in login_page.error_message()
