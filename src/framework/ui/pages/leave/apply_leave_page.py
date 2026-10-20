from playwright.sync_api import Page

from framework.ui.components.date_picker import DatePicker
from framework.ui.components.dropdown import Dropdown
from framework.ui.pages.base_page import BasePage


class ApplyLeavePage(BasePage):
    path = "/web/index.php/leave/applyLeave"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.leave_type = Dropdown(page, page.locator(".oxd-select-text").first)
        date_inputs = page.locator(".oxd-date-input input")
        self.from_date = DatePicker(page, date_inputs.nth(0))
        self.to_date = DatePicker(page, date_inputs.nth(1))
        self.comments = page.locator("textarea")
        self.apply_button = page.get_by_role("button", name="Apply")
