import pytest
from playwright.sync_api import Page, expect

from framework.api.models.employee import Employee
from framework.ui.pages.pim.employee_list_page import EmployeeListPage


@pytest.mark.e2e
@pytest.mark.smoke
def test_employee_created_via_api_is_listed_in_pim(admin_page: Page, employee: Employee) -> None:
    pim = EmployeeListPage(admin_page).open()
    pim.employee_name.search_and_select(employee.last_name, employee.last_name)
    pim.search()

    expect(pim.results.row_containing(employee.last_name)).to_be_visible()
