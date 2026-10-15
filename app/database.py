"""SQLite schema and seed data for the demo shop (the application under test)."""
import os
import sqlite3

DEFAULT_DB = os.path.join(os.path.dirname(__file__), "shop.db")

SCHEMA = """
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,          -- plain text: demo app only
    locked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL CHECK (price > 0),
    stock INTEGER NOT NULL CHECK (stock >= 0)
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL
);
"""

SEED_USERS = [
    (1, "standard_user", "Shop-Test#2026", 0),
    (2, "second_user", "Shop-Test#2026", 0),
    (3, "locked_out_user", "Shop-Test#2026", 1),
]

SEED_PRODUCTS = [
    (1, "Backpack", 29.99, 10),
    (2, "Bike Light", 9.99, 15),
    (3, "Bolt T-Shirt", 15.99, 20),
    (4, "Fleece Jacket", 49.99, 5),
    (5, "Onesie", 7.99, 25),
    (6, "Red T-Shirt", 15.99, 0),  # out of stock on purpose
]


def init_db(path: str = DEFAULT_DB) -> None:
    """Drop, recreate and re-seed all tables."""
    conn = sqlite3.connect(path, timeout=10)
    try:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO users VALUES (?,?,?,?)", SEED_USERS)
        conn.executemany("INSERT INTO products VALUES (?,?,?,?)", SEED_PRODUCTS)
        conn.commit()
    finally:
        conn.close()
