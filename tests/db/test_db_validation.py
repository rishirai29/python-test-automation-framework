"""Backend validation: assert on the SQLite database directly, before and after API/UI actions."""
import sqlite3

import pytest

pytestmark = [pytest.mark.db]


def test_seed_data_has_expected_row_counts(db):
    assert db.scalar("SELECT COUNT(*) FROM products") == 6
    assert db.scalar("SELECT COUNT(*) FROM users") == 3
    assert db.scalar("SELECT COUNT(*) FROM orders") == 0


def test_locked_out_user_is_flagged_in_database(db):
    assert db.scalar("SELECT locked FROM users WHERE username = 'locked_out_user'") == 1
    assert db.scalar("SELECT COUNT(*) FROM users WHERE locked = 1") == 1


def test_product_prices_are_positive_and_stock_non_negative(db):
    assert db.scalar("SELECT COUNT(*) FROM products WHERE price <= 0 OR stock < 0") == 0


def test_duplicate_username_is_rejected_by_unique_constraint(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO users(username, password, locked) VALUES ('standard_user', 'x', 0)")


def test_negative_stock_is_rejected_by_check_constraint(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE products SET stock = -1 WHERE id = 1")


def test_api_order_is_persisted_with_matching_items(auth_api, db):
    order = auth_api.create_order([{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]).json()
    row = db.query("SELECT * FROM orders WHERE id = ?", (order["id"],))[0]
    assert row["status"] == "CREATED"
    items = db.query("SELECT product_id, quantity FROM order_items WHERE order_id = ? ORDER BY product_id", (order["id"],))
    assert items == [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]


def test_order_total_equals_sum_of_line_items(auth_api, db):
    order_id = auth_api.create_order([{"product_id": 1, "quantity": 2}, {"product_id": 4, "quantity": 1}]).json()["id"]
    total = db.scalar("SELECT total FROM orders WHERE id = ?", (order_id,))
    line_sum = db.scalar("SELECT SUM(quantity * unit_price) FROM order_items WHERE order_id = ?", (order_id,))
    assert total == pytest.approx(line_sum)


def test_placing_an_order_decrements_stock(auth_api, db):
    auth_api.create_order([{"product_id": 1, "quantity": 3}])
    assert db.scalar("SELECT stock FROM products WHERE id = 1") == 7


def test_cancelling_an_order_restores_stock(auth_api, db):
    order_id = auth_api.create_order([{"product_id": 1, "quantity": 3}]).json()["id"]
    auth_api.cancel_order(order_id)
    assert db.scalar("SELECT stock FROM products WHERE id = 1") == 10
    assert db.scalar("SELECT status FROM orders WHERE id = ?", (order_id,)) == "CANCELLED"


def test_failed_order_does_not_change_stock_or_create_rows(auth_api, db):
    auth_api.create_order([{"product_id": 4, "quantity": 99}])
    assert db.scalar("SELECT stock FROM products WHERE id = 4") == 5
    assert db.scalar("SELECT COUNT(*) FROM orders") == 0
