from playwright.sync_api import Page

from framework.ui.components.autocomplete import Autocomplete
from framework.ui.components.dropdown import Dropdown
from framework.ui.pages.base_page import BasePage


class AddUserPage(BasePage):
    path = "/web/index.php/admin/saveSystemUser"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        dropdowns = page.locator(".oxd-select-text")
        self.user_role = Dropdown(page, dropdowns.nth(0))
        self.employee_name = Autocomplete(page, page.get_by_placeholder("Type for hints..."))
        self.status = Dropdown(page, dropdowns.nth(1))
        self.username = page.locator(".oxd-input-group", has_text="Username").locator("input")
        password_row = page.locator(".oxd-form-row.user-password-row")
        self.password = password_row.locator("input").nth(0)
        self.confirm_password = password_row.locator("input").nth(1)
        self.save_button = page.get_by_role("button", name="Save")

    def save(self) -> None:
        self.save_button.click()
