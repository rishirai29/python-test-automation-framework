"""Small Flask shop: web UI + REST API on top of SQLite. This is the system under test."""
import functools
import os
import secrets
import sqlite3
from contextlib import closing

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session

from app.database import DEFAULT_DB, init_db

SORTS = {
    "az": "name ASC",
    "za": "name DESC",
    "lohi": "price ASC, id ASC",
    "hilo": "price DESC, id ASC",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "demo-secret-key"
    tokens: dict[str, int] = {}

    def conn():
        c = sqlite3.connect(os.environ.get("DB_PATH", DEFAULT_DB), timeout=10)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        return c

    def order_payload(order_id: int):
        with closing(conn()) as c:
            o = c.execute(
                "SELECT o.*, u.username FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?",
                (order_id,),
            ).fetchone()
            if o is None:
                return None
            items = c.execute(
                "SELECT product_id, quantity, unit_price FROM order_items WHERE order_id=? ORDER BY id",
                (order_id,),
            ).fetchall()
        return {
            "id": o["id"],
            "user": o["username"],
            "status": o["status"],
            "total": o["total"],
            "items": [dict(i) for i in items],
        }

    def place_order(c, user_id: int, wanted: dict[int, int]):
        """Validate stock, create the order, decrement stock. Returns (order_id, error_response)."""
        lines, total = [], 0.0
        for pid, qty in wanted.items():
            p = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
            if p is None:
                return None, (jsonify(error=f"Product {pid} not found"), 404)
            if p["stock"] < qty:
                return None, (jsonify(error=f"Insufficient stock for product {pid}"), 409)
            lines.append((p, qty))
            total += p["price"] * qty
        cur = c.execute(
            "INSERT INTO orders(user_id,total,status) VALUES (?,?,?)",
            (user_id, round(total, 2), "CREATED"),
        )
        for p, qty in lines:
            c.execute(
                "INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES (?,?,?,?)",
                (cur.lastrowid, p["id"], qty, p["price"]),
            )
            c.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, p["id"]))
        c.commit()
        return cur.lastrowid, None

    # ------------------------------------------------------------------ REST API
    def api_auth(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            header = request.headers.get("Authorization", "")
            uid = tokens.get(header[7:]) if header.startswith("Bearer ") else None
            if uid is None:
                return jsonify(error="Missing or invalid token"), 401
            g.user_id = uid
            return fn(*a, **k)
        return wrapper

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.post("/api/auth/login")
    def api_login():
        data = request.get_json(silent=True) or {}
        username, password = data.get("username"), data.get("password")
        if not username or not password:
            return jsonify(error="username and password are required"), 400
        with closing(conn()) as c:
            u = c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        if u is None:
            return jsonify(error="Invalid credentials"), 401
        if u["locked"]:
            return jsonify(error="User is locked out"), 403
        token = secrets.token_hex(16)
        tokens[token] = u["id"]
        return jsonify(token=token, user={"id": u["id"], "username": u["username"]})

    @app.get("/api/products")
    def api_products():
        sql, params = "SELECT * FROM products WHERE 1=1", []
        if request.args.get("max_price"):
            sql += " AND price <= ?"
            params.append(float(request.args["max_price"]))
        if request.args.get("in_stock") == "true":
            sql += " AND stock > 0"
        if request.args.get("q"):
            sql += " AND name LIKE ?"
            params.append(f"%{request.args['q']}%")
        with closing(conn()) as c:
            rows = c.execute(sql + " ORDER BY id", params).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/api/products/<int:pid>")
    def api_product(pid):
        with closing(conn()) as c:
            p = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        return (jsonify(dict(p)), 200) if p else (jsonify(error="Product not found"), 404)

    @app.post("/api/orders")
    @api_auth
    def api_create_order():
        data = request.get_json(silent=True) or {}
        items = data.get("items")
        if not isinstance(items, list) or not items:
            return jsonify(error="items must be a non-empty list"), 400
        wanted: dict[int, int] = {}
        for it in items:
            pid = it.get("product_id") if isinstance(it, dict) else None
            qty = it.get("quantity") if isinstance(it, dict) else None
            ok = all(isinstance(v, int) and not isinstance(v, bool) for v in (pid, qty))
            if not ok or qty <= 0:
                return jsonify(error="each item needs integer product_id and quantity > 0"), 400
            wanted[pid] = wanted.get(pid, 0) + qty
        with closing(conn()) as c:
            order_id, err = place_order(c, g.user_id, wanted)
        if err:
            return err
        return jsonify(order_payload(order_id)), 201

    @app.get("/api/orders/<int:oid>")
    @api_auth
    def api_get_order(oid):
        o = order_payload(oid)
        if o is None:
            return jsonify(error="Order not found"), 404
        with closing(conn()) as c:
            owner = c.execute("SELECT user_id FROM orders WHERE id=?", (oid,)).fetchone()["user_id"]
        if owner != g.user_id:
            return jsonify(error="Forbidden"), 403
        return jsonify(o)

    @app.delete("/api/orders/<int:oid>")
    @api_auth
    def api_cancel_order(oid):
        with closing(conn()) as c:
            o = c.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
            if o is None:
                return jsonify(error="Order not found"), 404
            if o["user_id"] != g.user_id:
                return jsonify(error="Forbidden"), 403
            if o["status"] == "CANCELLED":
                return jsonify(error="Order already cancelled"), 409
            for it in c.execute("SELECT product_id, quantity FROM order_items WHERE order_id=?", (oid,)):
                c.execute("UPDATE products SET stock = stock + ? WHERE id=?", (it["quantity"], it["product_id"]))
            c.execute("UPDATE orders SET status='CANCELLED' WHERE id=?", (oid,))
            c.commit()
        return jsonify(order_payload(oid))

    # ------------------------------------------------------------------ Web UI
    def login_required(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            if "user_id" not in session:
                flash("You can only access this page when you are logged in.")
                return redirect("/login")
            return fn(*a, **k)
        return wrapper

    @app.get("/")
    def index():
        return redirect("/inventory" if "user_id" in session else "/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username:
                error = "Username is required"
            elif not password:
                error = "Password is required"
            else:
                with closing(conn()) as c:
                    u = c.execute(
                        "SELECT * FROM users WHERE username=? AND password=?", (username, password)
                    ).fetchone()
                if u is None:
                    error = "Username and password do not match any user in this service"
                elif u["locked"]:
                    error = "Sorry, this user has been locked out."
                else:
                    session.clear()
                    session["user_id"], session["username"], session["cart"] = u["id"], u["username"], []
                    return redirect("/inventory")
        else:
            msgs = session.pop("_flashes", None)
            if msgs:
                error = msgs[0][1]
        return render_template("login.html", error=error)

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    @app.get("/inventory")
    @login_required
    def inventory():
        sort = request.args.get("sort", "az")
        order = SORTS.get(sort, SORTS["az"])
        with closing(conn()) as c:
            products = c.execute(f"SELECT * FROM products ORDER BY {order}").fetchall()
        return render_template("inventory.html", products=products, cart=session["cart"], sort=sort)

    @app.post("/cart/<action>/<int:pid>")
    @login_required
    def cart_change(action, pid):
        cart = list(session["cart"])
        with closing(conn()) as c:
            p = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if action == "add" and p and p["stock"] > 0 and pid not in cart:
            cart.append(pid)
        elif action == "remove" and pid in cart:
            cart.remove(pid)
        session["cart"] = cart
        return redirect(request.form.get("next") or "/inventory")

    @app.get("/cart")
    @login_required
    def cart_page():
        with closing(conn()) as c:
            items = [c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone() for pid in session["cart"]]
        total = round(sum(i["price"] for i in items), 2)
        return render_template("cart.html", items=items, total=total, cart=session["cart"])

    @app.post("/checkout")
    @login_required
    def checkout():
        if not session["cart"]:
            return redirect("/cart")
        wanted = {pid: 1 for pid in session["cart"]}
        with closing(conn()) as c:
            order_id, err = place_order(c, session["user_id"], wanted)
        if err:
            return redirect("/cart")
        session["cart"] = []
        return redirect(f"/checkout-complete?order={order_id}")

    @app.get("/checkout-complete")
    @login_required
    def checkout_complete():
        return render_template("complete.html", order_id=request.args.get("order"), cart=session["cart"])

    return app


if __name__ == "__main__":
    init_db(os.environ.get("DB_PATH", DEFAULT_DB))
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5001")), debug=False, threaded=True)
