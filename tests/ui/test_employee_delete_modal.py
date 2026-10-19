import pytest
from playwright.sync_api import Page, expect

from framework.api.clients.employee_client import EmployeeClient
from framework.data.builders import EmployeeBuilder
from framework.ui.components.toast import Toast
from framework.ui.pages.pim.employee_list_page import EmployeeListPage


@pytest.mark.ui
@pytest.mark.destructive
def test_delete_employee_via_modal(admin_page: Page, employee_client: EmployeeClient) -> None:
    builder = EmployeeBuilder()
    created = employee_client.create(first_name=builder.first_name, last_name=builder.last_name)

    pim = EmployeeListPage(admin_page).open()
    pim.employee_name.search_and_select(created.last_name, created.last_name)
    pim.search()
    modal = pim.delete_row(created.last_name)
    modal.confirm()

    toast = Toast(admin_page)
    expect(toast.root).to_be_visible()
    assert "Successfully Deleted" in toast.message
