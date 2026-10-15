from framework.pages.playwright.base_page import BasePage


class LoginPage(BasePage):
    def open_login(self) -> "LoginPage":
        self.open("/login")
        return self

    def login(self, username: str, password: str) -> None:
        self.type("username", username)
        self.type("password", password)
        self.click("login-button")

    def error_message(self) -> str:
        return self.text("error")
