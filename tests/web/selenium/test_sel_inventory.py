import pytest

from framework.utils import is_sorted, load_json

pytestmark = [pytest.mark.web, pytest.mark.selenium]

PRODUCTS = load_json("products.json")


@pytest.mark.smoke
def test_inventory_lists_all_products(logged_in):
    assert sorted(logged_in.product_names()) == sorted(p["name"] for p in PRODUCTS)


@pytest.mark.regression
def test_default_sort_is_name_ascending(logged_in):
    assert is_sorted(logged_in.product_names())


@pytest.mark.regression
@pytest.mark.parametrize("sort_value", ["za", "lohi", "hilo"])
def test_sort_orders_products(logged_in, sort_value):
    logged_in.sort_by(sort_value)
    if sort_value == "za":
        assert is_sorted(logged_in.product_names(), reverse=True)
    elif sort_value == "lohi":
        assert is_sorted(logged_in.product_prices())
    else:
        assert is_sorted(logged_in.product_prices(), reverse=True)


@pytest.mark.smoke
def test_add_to_cart_updates_badge(logged_in):
    logged_in.add_to_cart(1)
    assert logged_in.badge_count() == 1


@pytest.mark.regression
def test_adding_three_products_shows_badge_three(logged_in):
    for product_id in (1, 2, 3):
        logged_in.add_to_cart(product_id)
    assert logged_in.badge_count() == 3


@pytest.mark.regression
def test_remove_from_cart_clears_badge(logged_in):
    logged_in.add_to_cart(1)
    logged_in.remove_from_cart(1)
    assert logged_in.badge_count() == 0


@pytest.mark.regression
def test_out_of_stock_product_cannot_be_added(logged_in):
    assert not logged_in.is_add_enabled(6)
