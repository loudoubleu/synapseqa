from playwright.sync_api import Page

from framework.ui.pages.base_page import BasePage
from framework.ui.pages.dashboard_page import DashboardPage


class LoginPage(BasePage):
    path = "/web/index.php/auth/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username = page.get_by_placeholder("Username")
        self.password = page.get_by_placeholder("Password")
        self.submit = page.get_by_role("button", name="Login")
        self.invalid_credentials_message = page.get_by_text("Invalid credentials")
        self.required_messages = page.get_by_text("Required")

    def login(self, username: str, password: str) -> DashboardPage:
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()
        return DashboardPage(self.page)
