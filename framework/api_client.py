"""Thin wrapper around requests.Session for the shop REST API."""
import requests

from framework.config import TIMEOUT


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token = None

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", TIMEOUT)
        headers = {**self._headers(), **kwargs.pop("headers", {})}
        return self.session.request(method, self._url(path), headers=headers, **kwargs)

    # --- auth
    def login(self, username: str, password: str) -> requests.Response:
        return self.request("POST", "/api/auth/login", json={"username": username, "password": password})

    def authenticate(self, username: str, password: str) -> "ApiClient":
        resp = self.login(username, password)
        resp.raise_for_status()
        self.token = resp.json()["token"]
        return self

    # --- products
    def list_products(self, **params) -> requests.Response:
        return self.request("GET", "/api/products", params=params)

    def get_product(self, product_id: int) -> requests.Response:
        return self.request("GET", f"/api/products/{product_id}")

    # --- orders
    def create_order(self, items: list) -> requests.Response:
        return self.request("POST", "/api/orders", json={"items": items})

    def get_order(self, order_id: int) -> requests.Response:
        return self.request("GET", f"/api/orders/{order_id}")

    def cancel_order(self, order_id: int) -> requests.Response:
        return self.request("DELETE", f"/api/orders/{order_id}")
