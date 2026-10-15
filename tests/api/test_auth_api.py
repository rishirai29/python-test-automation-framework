import pytest

from framework import config
from framework.schema import validate

pytestmark = [pytest.mark.api]


@pytest.mark.smoke
def test_health_endpoint_is_up(api):
    resp = api.request("GET", "/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.smoke
def test_login_with_valid_credentials_returns_token(api):
    resp = api.login(*config.VALID_USER)
    assert resp.status_code == 200
    assert resp.json()["user"]["username"] == "standard_user"


def test_login_response_matches_json_schema(api):
    validate(api.login(*config.VALID_USER).json(), "login_response")


@pytest.mark.parametrize(
    "username,password",
    [("standard_user", "wrong_pw"), ("unknown_user", "Shop-Test#2026"), ("STANDARD_USER", "Shop-Test#2026")],
    ids=["wrong-password", "unknown-user", "username-is-case-sensitive"],
)
def test_login_with_invalid_credentials_returns_401(api, username, password):
    resp = api.login(username, password)
    assert resp.status_code == 401
    validate(resp.json(), "error")


def test_locked_out_user_gets_403(api):
    resp = api.login(*config.LOCKED_USER)
    assert resp.status_code == 403
    assert "locked" in resp.json()["error"].lower()


@pytest.mark.parametrize(
    "payload", [{}, {"username": "standard_user"}, {"password": "Shop-Test#2026"}],
    ids=["empty-body", "missing-password", "missing-username"],
)
def test_login_with_missing_fields_returns_400(api, payload):
    resp = api.request("POST", "/api/auth/login", json=payload)
    assert resp.status_code == 400
    validate(resp.json(), "error")
