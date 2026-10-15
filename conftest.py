"""Command-line switches for live demos (project-level, loaded before the tests)."""
from framework import config as settings


def pytest_addoption(parser):
    group = parser.getgroup("live demo")
    group.addoption("--headed", action="store_true", help="show the browser window while the tests run")
    group.addoption("--slow-mo", type=int, default=None, metavar="MS",
                    help="wait MS milliseconds before every browser action (default 400 when --headed)")
    group.addoption("--keep-open", action="store_true",
                    help="after each UI test keep the browser open until you press Enter (implies --headed)")


def pytest_configure(config):
    keep_open = config.getoption("--keep-open")
    headed = config.getoption("--headed") or keep_open
    slow_mo = config.getoption("--slow-mo")
    if headed:
        settings.HEADLESS = False
    if keep_open:
        settings.KEEP_OPEN = True
    if slow_mo is not None:
        settings.SLOWMO_MS = slow_mo
    elif headed and settings.SLOWMO_MS == 0:
        settings.SLOWMO_MS = 400
