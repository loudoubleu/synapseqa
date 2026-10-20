import pytest
from playwright.sync_api import Browser, expect

from framework.api.clients.leave_client import ANNUAL_LEAVE_TYPE_ID, LeaveClient
from framework.api.clients.user_client import ESS_ROLE_ID, UserClient
from framework.api.models.employee import Employee
from framework.data.builders import UserBuilder
from framework.ui.pages.leave.apply_leave_page import ApplyLeavePage
from framework.ui.pages.login_page import LoginPage


@pytest.mark.e2e
@pytest.mark.destructive
def test_leave_applied_in_ui_shows_via_api(
    browser: Browser,
    base_url: str,
    employee: Employee,
    user_client: UserClient,
    leave_client: LeaveClient,
) -> None:
    builder = UserBuilder()
    user = user_client.create(
        username=builder.username,
        password=builder.password,
        user_role_id=ESS_ROLE_ID,
        emp_number=employee.emp_number,
    )
    leave_client.grant_entitlement(
        emp_number=employee.emp_number,
        leave_type_id=ANNUAL_LEAVE_TYPE_ID,
        from_date="2026-01-01",
        to_date="2026-12-31",
        days=10,
    )

    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    login_page = LoginPage(page).open()
    dashboard = login_page.login(user.user_name, builder.password)
    expect(dashboard.heading).to_be_visible()

    apply_page = ApplyLeavePage(page).open()
    apply_page.leave_type.choose("Annual Leave")
    apply_page.from_date.set_date("2026-11-20")
    apply_page.to_date.set_date("2026-11-20")
    apply_page.apply_button.click()
    expect(page.get_by_text("Successfully Saved")).to_be_visible()

    # Verify via the API, reusing the same authenticated session (the leave-requests GET is
    # self-scoped to whichever user the request context is authenticated as -- confirmed against
    # the running app).
    response = context.request.get(
        "/web/index.php/api/v2/leave/leave-requests",
        params={"fromDate": "2026-01-01", "toDate": "2026-12-31"},
    )
    assert response.status == 200
    applied_dates = [r["dates"]["fromDate"] for r in response.json()["data"]]
    assert "2026-11-20" in applied_dates

    context.close()
