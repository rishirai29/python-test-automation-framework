# Python Test Automation Framework – Web, API & Database

[![Test Automation](https://github.com/rishirai29/python-test-automation-framework/actions/workflows/tests.yml/badge.svg)](https://github.com/rishirai29/python-test-automation-framework/actions/workflows/tests.yml)

A reusable **PyTest** framework that tests a small shop application at three layers – **web UI** (Selenium WebDriver and Playwright, both in Python), **REST API** (Requests + JSON Schema) and **database** (SQL assertions on SQLite) – plus **BDD** scenarios with pytest-bdd.
Everything runs on every push through **GitHub Actions**, which publishes an HTML report.

The application under test (`app/`) is a Flask + SQLite demo shop bundled in this repo, so the suite is fully self-contained and needs no external website.

## What is covered

| Layer | Tooling | Tests |
|---|---|---|
| Web UI – Selenium | Selenium WebDriver, Page Object Model | 23 |
| Web UI – Playwright | Playwright (sync API), Page Object Model | 23 |
| REST API | `requests`, JSON Schema validation (`jsonschema`) | 49 |
| Database | direct SQL assertions on SQLite (constraints, stock, totals, referential integrity) | 10 |
| BDD | pytest-bdd (Gherkin), UI steps on Playwright, API steps on the API client | 13 |
| **Total** | | **118** |

Features exercised: login (valid, invalid, locked-out, empty fields, logout, protected pages), product catalogue and sorting, cart, checkout, order creation/cancellation, stock rules, authentication and authorisation (401/403), input validation (400), conflict handling (409).

## Framework design

```
app/                 demo shop (Flask + SQLite) – the system under test
framework/
  config.py          env-driven settings (BASE_URL, HEADLESS, TIMEOUT, ...)
  api_client.py      reusable REST client (session, auth token, endpoints)
  db.py              SQLite helper for backend validation
  schema.py          JSON Schema validation helper
  utils.py           data loading and small helpers
  pages/selenium/    Page Objects for Selenium (explicit waits, stale-element handling)
  pages/playwright/  Page Objects for Playwright
schemas/             JSON Schemas (product, order, login response, error)
testdata/            data-driven inputs (products, login cases)
tests/
  conftest.py        fixtures: app server, DB reset per test, API client, browsers, failure screenshots
  web/selenium/      UI tests (Selenium)
  web/playwright/    UI tests (Playwright)
  api/               API tests
  db/                database validation tests
  bdd/               Gherkin features + step definitions
.github/workflows/   CI pipeline
```

Key practices: Page Object Model, fixtures for setup/teardown, parametrisation driven by JSON test data, an isolated seeded database for every test, markers (`smoke`, `regression`, `web`, `api`, `db`, `bdd`), screenshots embedded in the HTML report on failure.

## Run it locally

Requires Python 3.10+ and Google Chrome (for Selenium).

```bash
git clone https://github.com/rishirai29/python-test-automation-framework.git
cd python-test-automation-framework
python -m venv .venv
# Windows:  .venv\Scripts\activate        macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
pytest
```

Useful commands:

```bash
pytest -m smoke                 # quick sanity set
pytest -m "api or db"           # backend only
pytest -m selenium              # Selenium UI only
pytest tests/bdd                # BDD scenarios
HEADLESS=false pytest -m web    # watch the browser (Windows PowerShell: $env:HEADLESS="false")
```

Reports are written to `reports/report.html` (self-contained) and `reports/junit.xml`.

## CI

`.github/workflows/tests.yml` installs dependencies and Playwright Chromium, runs the full suite and uploads `reports/` as the **test-reports** artifact on every push and pull request.
