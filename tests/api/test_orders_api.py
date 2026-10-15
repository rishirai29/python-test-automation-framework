import pytest

from framework import config
from framework.api_client import ApiClient
from framework.schema import validate

pytestmark = [pytest.mark.api]


@pytest.mark.smoke
def test_create_order_returns_201_and_valid_payload(auth_api):
    resp = auth_api.create_order([{"product_id": 1, "quantity": 2}])
    assert resp.status_code == 201
    body = resp.json()
    validate(body, "order")
    assert body["status"] == "CREATED"
    assert body["user"] == "standard_user"


@pytest.mark.parametrize(
    "items,expected_total",
    [
        ([{"product_id": 1, "quantity": 1}], 29.99),
        ([{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 3}], 89.95),
        ([{"product_id": 5, "quantity": 4}], 31.96),
    ],
    ids=["single-item", "two-products", "quantity-four"],
)
def test_order_total_is_calculated_correctly(auth_api, items, expected_total):
    assert auth_api.create_order(items).json()["total"] == pytest.approx(expected_total)


def test_create_order_without_token_returns_401(api):
    assert api.create_order([{"product_id": 1, "quantity": 1}]).status_code == 401


def test_create_order_with_invalid_token_returns_401(api):
    api.token = "not-a-real-token"
    assert api.create_order([{"product_id": 1, "quantity": 1}]).status_code == 401


@pytest.mark.parametrize(
    "items",
    [[], [{"product_id": 1, "quantity": 0}], [{"product_id": 1, "quantity": -3}], [{"product_id": "1", "quantity": 1}]],
    ids=["empty-list", "zero-quantity", "negative-quantity", "product-id-not-int"],
)
def test_create_order_with_invalid_payload_returns_400(auth_api, items):
    resp = auth_api.create_order(items)
    assert resp.status_code == 400
    validate(resp.json(), "error")


def test_create_order_with_unknown_product_returns_404(auth_api):
    assert auth_api.create_order([{"product_id": 999, "quantity": 1}]).status_code == 404


def test_create_order_with_insufficient_stock_returns_409(auth_api):
    resp = auth_api.create_order([{"product_id": 4, "quantity": 99}])
    assert resp.status_code == 409
    assert "stock" in resp.json()["error"].lower()


def test_out_of_stock_product_cannot_be_ordered(auth_api):
    assert auth_api.create_order([{"product_id": 6, "quantity": 1}]).status_code == 409


def test_get_own_order(auth_api):
    created = auth_api.create_order([{"product_id": 2, "quantity": 1}]).json()
    resp = auth_api.get_order(created["id"])
    assert resp.status_code == 200
    assert resp.json() == created


def test_get_unknown_order_returns_404(auth_api):
    assert auth_api.get_order(12345).status_code == 404


def test_user_cannot_read_another_users_order(base_url, auth_api):
    order_id = auth_api.create_order([{"product_id": 1, "quantity": 1}]).json()["id"]
    other = ApiClient(base_url).authenticate(*config.SECOND_USER)
    assert other.get_order(order_id).status_code == 403


def test_cancel_order_sets_status_cancelled(auth_api):
    order_id = auth_api.create_order([{"product_id": 1, "quantity": 1}]).json()["id"]
    resp = auth_api.cancel_order(order_id)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


def test_cancelling_an_order_twice_returns_409(auth_api):
    order_id = auth_api.create_order([{"product_id": 1, "quantity": 1}]).json()["id"]
    auth_api.cancel_order(order_id)
    assert auth_api.cancel_order(order_id).status_code == 409
