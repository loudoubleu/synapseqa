from playwright.sync_api import Page

from framework.ui.pages.base_page import BasePage
from framework.ui.pages.pim.personal_details_page import PersonalDetailsPage


class AddEmployeePage(BasePage):
    path = "/web/index.php/pim/addEmployee"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.first_name = page.get_by_placeholder("First Name")
        self.middle_name = page.get_by_placeholder("Middle Name")
        self.last_name = page.get_by_placeholder("Last Name")
        self.employee_id = page.locator(".oxd-input-group", has_text="Employee Id").locator("input")
        self.photo_upload = page.locator("input[type=file]")
        self.save_button = page.get_by_role("button", name="Save")

    def fill_name(self, *, first_name: str, last_name: str, middle_name: str = "") -> "AddEmployeePage":
        self.first_name.fill(first_name)
        if middle_name:
            self.middle_name.fill(middle_name)
        self.last_name.fill(last_name)
        # The server's auto-suggested Employee Id has been observed to collide with one
        # already in use (confirmed against the running app); clear it so the server
        # assigns a fresh one on save instead of rejecting with "Employee Id already exists".
        self.employee_id.fill("")
        return self

    def upload_photo(self, path: str) -> "AddEmployeePage":
        self.photo_upload.set_input_files(path)
        return self

    def save(self) -> PersonalDetailsPage:
        self.save_button.click()
        self.page.get_by_role("heading", name="Personal Details").wait_for()
        return PersonalDetailsPage(self.page)
