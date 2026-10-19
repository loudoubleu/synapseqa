import pytest
from playwright.sync_api import Page, Route, expect

from framework.ui.components.toast import Toast
from framework.ui.pages.pim.employee_list_page import EmployeeListPage


def _fail_with_server_error(route: Route) -> None:
    route.fulfill(
        status=500,
        content_type="application/json",
        body='{"error":{"message":"Internal Server Error"}}',
    )


@pytest.mark.ui
def test_employee_list_shows_error_toast_on_api_failure(admin_page: Page) -> None:
    admin_page.route("**/api/v2/pim/employees*", _fail_with_server_error)

    pim = EmployeeListPage(admin_page).open()

    toast = Toast(admin_page)
    expect(toast.root).to_be_visible()
    assert "Internal Server Error" in toast.message
    expect(pim.page.get_by_text("No Records Found")).to_be_visible()
