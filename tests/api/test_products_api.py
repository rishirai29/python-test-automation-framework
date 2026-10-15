import pytest

from framework.schema import validate
from framework.utils import load_json

pytestmark = [pytest.mark.api]

PRODUCTS = load_json("products.json")


@pytest.mark.smoke
def test_list_products_returns_200_and_json(api):
    resp = api.list_products()
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("application/json")


def test_list_products_matches_expected_catalogue(api):
    assert api.list_products().json() == PRODUCTS


@pytest.mark.parametrize("product", PRODUCTS, ids=[p["name"] for p in PRODUCTS])
def test_each_listed_product_matches_json_schema(api, product):
    listed = {p["id"]: p for p in api.list_products().json()}
    validate(listed[product["id"]], "product")


@pytest.mark.regression
@pytest.mark.parametrize("product", PRODUCTS, ids=[p["name"] for p in PRODUCTS])
def test_get_product_by_id(api, product):
    resp = api.get_product(product["id"])
    assert resp.status_code == 200
    assert resp.json() == product


def test_unknown_product_returns_404(api):
    resp = api.get_product(999)
    assert resp.status_code == 404
    validate(resp.json(), "error")


@pytest.mark.parametrize("max_price,expected_count", [(10, 2), (16, 4), (100, 6)])
def test_filter_by_max_price(api, max_price, expected_count):
    products = api.list_products(max_price=max_price).json()
    assert len(products) == expected_count
    assert all(p["price"] <= max_price for p in products)


def test_filter_in_stock_excludes_out_of_stock_products(api):
    products = api.list_products(in_stock="true").json()
    assert len(products) == 5
    assert all(p["stock"] > 0 for p in products)


@pytest.mark.parametrize("query,expected", [("shirt", {"Bolt T-Shirt", "Red T-Shirt"}), ("zzz", set())])
def test_search_by_name(api, query, expected):
    assert {p["name"] for p in api.list_products(q=query).json()} == expected
