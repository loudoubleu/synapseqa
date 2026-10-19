from playwright.sync_api import Page

from framework.ui.components.autocomplete import Autocomplete
from framework.ui.components.data_table import DataTable
from framework.ui.components.modal import Modal
from framework.ui.pages.base_page import BasePage
from framework.ui.pages.pim.add_employee_page import AddEmployeePage


class EmployeeListPage(BasePage):
    path = "/web/index.php/pim/viewEmployeeList"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.employee_name = Autocomplete(page, page.get_by_placeholder("Type for hints...").first)
        self.search_button = page.get_by_role("button", name="Search")
        self.add_button = page.get_by_role("button", name="Add")
        self.results = DataTable(page, page.locator(".oxd-table"))

    def search(self) -> None:
        self.search_button.click()
        self.page.wait_for_load_state("networkidle")

    def delete_row(self, row_text: str) -> Modal:
        row = self.results.row_containing(row_text)
        row.get_by_role("button").last.click()
        return Modal(self.page)

    def open_add_employee(self) -> AddEmployeePage:
        self.add_button.click()
        return AddEmployeePage(self.page)
