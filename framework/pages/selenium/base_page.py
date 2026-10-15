"""Base page object for Selenium: explicit waits, data-test locators and reload-safe interactions."""
import time

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from framework.config import TIMEOUT

# Errors that just mean "the page was re-rendering while we touched it" -> safe to retry.
_TRANSIENT = (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
)


class BasePage:
    def __init__(self, driver, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, TIMEOUT)

    @staticmethod
    def _by(name: str):
        return By.CSS_SELECTOR, f'[data-test="{name}"]'

    def _retry(self, action):
        """Run `action` until it succeeds or TIMEOUT expires, tolerating page re-renders."""
        deadline = time.time() + TIMEOUT
        while True:
            try:
                return action()
            except _TRANSIENT:
                pass
            except WebDriverException as exc:
                if "does not belong to the document" not in str(exc):
                    raise
            if time.time() > deadline:
                return action()  # final attempt, let the real error surface
            time.sleep(0.1)

    # ---- navigation
    def open(self, path: str = "") -> None:
        self.driver.get(f"{self.base_url}{path}")

    def current_url(self) -> str:
        return self.driver.current_url

    def _page_marker(self):
        return self._retry(lambda: self.driver.find_element(By.TAG_NAME, "html"))

    def wait_for_navigation(self, old_page) -> None:
        """After an action, wait for the old DOM to be replaced and the new page to finish loading."""
        try:
            WebDriverWait(self.driver, 3).until(EC.staleness_of(old_page))
        except (TimeoutException, WebDriverException):
            pass  # the action did not navigate (or the old node is already gone)
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    # ---- elements
    def element(self, name: str):
        def _visible():
            el = self.driver.find_element(*self._by(name))
            if not el.is_displayed():
                raise NoSuchElementException(f"{name} not visible")
            return el

        return self._retry(_visible)

    def exists(self, name: str) -> bool:
        return self._retry(lambda: len(self.driver.find_elements(*self._by(name))) > 0)

    def click(self, name: str) -> None:
        old_page = self._page_marker()
        self._retry(lambda: self.driver.find_element(*self._by(name)).click())
        self.wait_for_navigation(old_page)

    def type(self, name: str, text: str) -> None:
        def _type():
            field = self.driver.find_element(*self._by(name))
            field.clear()
            field.send_keys(text)

        self._retry(_type)

    def text(self, name: str) -> str:
        return self._retry(lambda: self.element(name).text.strip())

    def texts(self, css: str) -> list[str]:
        return self._retry(lambda: [e.text.strip() for e in self.driver.find_elements(By.CSS_SELECTOR, css)])
