import pytest

pytestmark = [pytest.mark.web, pytest.mark.selenium]


@pytest.mark.regression
def test_cart_lists_added_products(logged_in, cart_page):
    logged_in.add_to_cart(1)
    logged_in.add_to_cart(3)
    logged_in.open_cart()
    assert cart_page.item_names() == ["Backpack", "Bolt T-Shirt"]


@pytest.mark.regression
def test_cart_total_is_sum_of_prices(logged_in, cart_page):
    logged_in.add_to_cart(1)
    logged_in.add_to_cart(2)
    logged_in.open_cart()
    assert cart_page.total() == pytest.approx(39.98)


@pytest.mark.regression
def test_remove_item_from_cart(logged_in, cart_page):
    logged_in.add_to_cart(1)
    logged_in.open_cart()
    cart_page.remove(1)
    assert cart_page.item_names() == []


@pytest.mark.smoke
def test_checkout_shows_confirmation(logged_in, cart_page):
    logged_in.add_to_cart(1)
    logged_in.open_cart()
    cart_page.checkout()
    assert cart_page.confirmation_header() == "Thank you for your order!"


@pytest.mark.regression
@pytest.mark.db
def test_checkout_creates_order_in_database(logged_in, cart_page, db):
    logged_in.add_to_cart(1)
    logged_in.add_to_cart(4)
    logged_in.open_cart()
    cart_page.checkout()
    order_id = cart_page.order_id()
    order = db.query("SELECT * FROM orders WHERE id = ?", (order_id,))[0]
    assert order["status"] == "CREATED"
    assert order["total"] == pytest.approx(79.98)
    assert db.scalar("SELECT COUNT(*) FROM order_items WHERE order_id = ?", (order_id,)) == 2
    assert db.scalar("SELECT stock FROM products WHERE id = 1") == 9


@pytest.mark.regression
def test_checkout_is_disabled_for_empty_cart(logged_in, cart_page):
    logged_in.open_cart()
    assert not cart_page.is_checkout_enabled()
