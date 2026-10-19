from playwright.sync_api import Page

from framework.ui.components.autocomplete import Autocomplete
from framework.ui.components.data_table import DataTable
from framework.ui.pages.admin.add_user_page import AddUserPage
from framework.ui.pages.base_page import BasePage


class UserManagementPage(BasePage):
    path = "/web/index.php/admin/viewSystemUsers"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username = page.locator(".oxd-input-group", has_text="Username").locator("input")
        self.employee_name = Autocomplete(page, page.get_by_placeholder("Type for hints..."))
        self.search_button = page.get_by_role("button", name="Search")
        self.add_button = page.get_by_role("button", name="Add")
        self.results = DataTable(page, page.locator(".oxd-table"))

    def search(self) -> None:
        self.search_button.click()
        self.page.wait_for_load_state("networkidle")

    def open_add_user(self) -> AddUserPage:
        self.add_button.click()
        return AddUserPage(self.page)
