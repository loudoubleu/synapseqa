from playwright.sync_api import Page

from framework.ui.components.data_table import DataTable
from framework.ui.pages.base_page import BasePage


class LeaveListPage(BasePage):
    path = "/web/index.php/leave/viewLeaveList"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.search_button = page.get_by_role("button", name="Search")
        self.results = DataTable(page, page.locator(".oxd-table"))

    def search(self) -> None:
        self.search_button.click()
        self.page.wait_for_load_state("networkidle")

    def approve_row(self, row_text: str) -> None:
        self.results.row_containing(row_text).get_by_role("button", name="Approve").click()

    def reject_row(self, row_text: str) -> None:
        self.results.row_containing(row_text).get_by_role("button", name="Reject").click()
