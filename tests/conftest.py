"""Shared fixtures: app server, test data reset, API client, DB access, browsers, failure screenshots."""
import base64
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from app.database import init_db
from framework import config
from framework.api_client import ApiClient
from framework.db import Database


# --------------------------------------------------------------------------- system under test
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    return str(tmp_path_factory.mktemp("data") / "shop_test.db")


@pytest.fixture(scope="session")
def base_url(db_path):
    """Start the bundled demo app on a free port (or use BASE_URL if provided)."""
    if config.EXTERNAL_BASE_URL:
        yield config.EXTERNAL_BASE_URL.rstrip("/")
        return
    init_db(db_path)
    port = _free_port()
    env = {**__import__("os").environ, "DB_PATH": db_path, "PORT": str(port)}
    proc = subprocess.Popen([sys.executable, "-m", "app.server"], cwd=config.ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            if requests.get(f"{url}/api/health", timeout=1).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.2)
    else:
        proc.kill()
        raise RuntimeError("Demo app did not start in time")
    yield url
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(autouse=True)
def reset_data(base_url, db_path):
    """Every test starts from the same seeded database."""
    if not config.EXTERNAL_BASE_URL:
        init_db(db_path)


@pytest.fixture
def db(db_path):
    return Database(db_path)


@pytest.fixture
def api(base_url):
    return ApiClient(base_url)


@pytest.fixture
def auth_api(base_url):
    return ApiClient(base_url).authenticate(*config.VALID_USER)


# --------------------------------------------------------------------------- live-demo helper
def _pause_for_viewing(request) -> None:
    """With --keep-open: leave the browser open after the test until the user presses Enter."""
    if not config.KEEP_OPEN:
        return
    capman = request.config.pluginmanager.getplugin("capturemanager")
    message = f"\n>>> '{request.node.name}' finished. Look at the browser, then press Enter to close it... "

    def _ask():
        print(message, end="", flush=True)
        try:
            sys.__stdin__.readline()  # the real keyboard input, even while pytest captures output
        except (OSError, ValueError):
            pass

    if capman:
        with capman.global_and_fixture_disabled():
            _ask()
    else:
        _ask()


# --------------------------------------------------------------------------- Selenium
class _SlowChrome(webdriver.Chrome):
    """Chrome that waits SLOWMO milliseconds before every command, so a live demo is easy to follow."""

    def execute(self, driver_command, params=None):
        time.sleep(config.SLOWMO_MS / 1000)
        return super().execute(driver_command, params)


@pytest.fixture
def driver(request):
    options = Options()
    if config.HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    # Real Chrome shows password-manager / data-breach pop-ups after a login form is submitted;
    # they can swallow clicks, so switch them off for test runs.
    options.add_argument("--disable-features=PasswordLeakDetection,PasswordManagerOnboarding,SafeBrowsingEnhancedProtection")
    options.add_argument("--disable-save-password-bubble")
    options.add_argument("--incognito")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        },
    )
    if config.CHROME_BIN:
        options.binary_location = config.CHROME_BIN
    service = Service(executable_path=config.CHROMEDRIVER_PATH) if config.CHROMEDRIVER_PATH else Service()
    chrome_class = _SlowChrome if config.SLOWMO_MS else webdriver.Chrome
    drv = chrome_class(options=options, service=service)
    drv.implicitly_wait(0)
    yield drv
    _pause_for_viewing(request)
    drv.quit()


# --------------------------------------------------------------------------- Playwright
@pytest.fixture(scope="session")
def pw_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS, args=["--no-sandbox"], slow_mo=config.SLOWMO_MS)
        yield browser
        browser.close()


@pytest.fixture
def pw_page(pw_browser, request):
    context = pw_browser.new_context(viewport={"width": 1280, "height": 900})
    context.set_default_timeout(config.TIMEOUT * 1000)
    page = context.new_page()
    yield page
    _pause_for_viewing(request)
    context.close()


# --------------------------------------------------------------------------- reporting
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On failure, save a screenshot and embed it in the HTML report."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or report.passed:
        return
    shot = None
    config.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe = item.nodeid.replace("/", "_").replace("::", "__").replace("[", "_").replace("]", "")
    path = Path(config.SCREENSHOT_DIR) / f"{safe}.png"
    try:
        if "driver" in item.funcargs:
            item.funcargs["driver"].save_screenshot(str(path))
            shot = path
        elif "pw_page" in item.funcargs:
            item.funcargs["pw_page"].screenshot(path=str(path))
            shot = path
    except Exception:  # never let reporting break the test run
        shot = None
    if shot and shot.exists():
        from pytest_html import extras
        report.extras = getattr(report, "extras", []) + [extras.png(base64.b64encode(shot.read_bytes()).decode())]
