from playwright.sync_api import Page

from framework.ui.components.date_picker import DatePicker
from framework.ui.components.dropdown import Dropdown
from framework.ui.pages.base_page import BasePage


class PersonalDetailsPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        dropdowns = page.locator(".oxd-select-text")
        self.nationality = Dropdown(page, dropdowns.nth(0))
        self.marital_status = Dropdown(page, dropdowns.nth(1))
        self.date_of_birth = DatePicker(page, page.locator(".oxd-date-input input").last)
        self.save_button = page.get_by_role("button", name="Save")
