"""Central configuration. Everything can be overridden with environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
TESTDATA_DIR = ROOT / "testdata"
SCHEMA_DIR = ROOT / "schemas"

# If BASE_URL is set the framework tests that environment; otherwise it starts the bundled demo app.
EXTERNAL_BASE_URL = os.getenv("BASE_URL")
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"
TIMEOUT = int(os.getenv("TIMEOUT", "10"))
CHROME_BIN = os.getenv("CHROME_BIN")            # optional custom Chrome/Chromium binary
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")  # optional; Selenium Manager is used if unset

VALID_USER = ("standard_user", "Shop-Test#2026")
SECOND_USER = ("second_user", "Shop-Test#2026")
LOCKED_USER = ("locked_out_user", "Shop-Test#2026")
