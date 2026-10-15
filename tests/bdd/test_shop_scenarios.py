"""pytest-bdd step definitions. UI steps run on Playwright, API steps use the requests-based client."""
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from framework import config
from framework.api_client import ApiClient
from framework.pages.playwright.cart_page import CartPage
from framework.pages.playwright.inventory_page import InventoryPage
from framework.pages.playwright.login_page import LoginPage

pytestmark = [pytest.mark.bdd]

scenarios(
    "features/login.feature",
    "features/cart.feature",
    "features/products_api.feature",
    "features/orders_api.feature",
)


# ------------------------------------------------------------------ UI steps
@pytest.fixture
def login_page(pw_page, base_url):
    return LoginPage(pw_page, base_url)


@pytest.fixture
def inventory_page(pw_page, base_url):
    return InventoryPage(pw_page, base_url)


@pytest.fixture
def cart_page(pw_page, base_url):
    return CartPage(pw_page, base_url)


@given("I am on the login page")
def on_login_page(login_page):
    login_page.open_login()


@given(parsers.parse('I am logged in as "{username}"'))
def logged_in_as(login_page, username):
    login_page.open_login()
    login_page.login(username, config.VALID_USER[1])


@when(parsers.parse('I log in as "{username}" with password "{password}"'))
def log_in(login_page, username, password):
    login_page.login(username, password)


@then("I should see the products page")
def see_products_page(inventory_page):
    assert inventory_page.title() == "Products"


@then(parsers.parse('I should see the error "{message}"'))
def see_error(login_page, message):
    assert login_page.error_message() == message


@given(parsers.parse("I have added product {product_id:d} to the cart"))
@when(parsers.parse("I add product {product_id:d} to the cart"))
def add_product(inventory_page, product_id):
    inventory_page.add_to_cart(product_id)


@when(parsers.parse("I remove product {product_id:d} from the cart"))
def remove_product(inventory_page, product_id):
    inventory_page.remove_from_cart(product_id)


@then(parsers.parse("the cart badge shows {count:d}"))
def badge_shows(inventory_page, count):
    assert inventory_page.badge_count() == count


@then("the cart badge is not shown")
def badge_hidden(inventory_page):
    assert inventory_page.badge_count() == 0


@when("I check out")
def check_out(inventory_page, cart_page):
    inventory_page.open_cart()
    cart_page.checkout()


@then("I should see the order confirmation")
def see_confirmation(cart_page):
    assert cart_page.confirmation_header() == "Thank you for your order!"


@then(parsers.parse('an order exists in the database for "{username}"'))
def order_in_db(db, username):
    count = db.scalar(
        "SELECT COUNT(*) FROM orders o JOIN users u ON u.id = o.user_id WHERE u.username = ?", (username,)
    )
    assert count == 1


# ------------------------------------------------------------------ API steps
@given(parsers.parse('I am authenticated as "{username}" via the API'), target_fixture="client")
def authenticated_client(base_url, username):
    return ApiClient(base_url).authenticate(username, config.VALID_USER[1])


@when("I request the product list", target_fixture="response")
def request_product_list(api):
    return api.list_products()


@when(parsers.parse("I request product {product_id:d}"), target_fixture="response")
def request_product(api, product_id):
    return api.get_product(product_id)


@when(parsers.parse("I order {quantity:d} units of product {product_id:d}"), target_fixture="response")
def order_units(client, quantity, product_id):
    return client.create_order([{"product_id": product_id, "quantity": quantity}])


@then(parsers.parse("the response status is {code:d}"))
def status_is(response, code):
    assert response.status_code == code


@then(parsers.parse("the response contains {count:d} products"))
def contains_products(response, count):
    assert len(response.json()) == count


@then(parsers.parse('the product name is "{name}"'))
def product_name(response, name):
    assert response.json()["name"] == name


@then(parsers.parse('the order status is "{status}"'))
def order_status(response, status):
    assert response.json()["status"] == status


@then(parsers.parse("the stock of product {product_id:d} is {stock:d} in the database"))
def stock_in_db(db, product_id, stock):
    assert db.scalar("SELECT stock FROM products WHERE id = ?", (product_id,)) == stock
