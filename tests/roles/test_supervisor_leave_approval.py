import pytest
from playwright.sync_api import Browser, expect

from framework.api.clients.employee_client import EmployeeClient
from framework.api.clients.leave_client import ANNUAL_LEAVE_TYPE_ID, LeaveClient
from framework.api.clients.user_client import ESS_ROLE_ID, UserClient
from framework.data.builders import EmployeeBuilder, UserBuilder
from framework.ui.pages.leave.leave_list_page import LeaveListPage
from framework.ui.pages.login_page import LoginPage


@pytest.mark.roles
@pytest.mark.destructive
def test_supervisor_can_approve_direct_reports_leave_request(
    browser: Browser,
    base_url: str,
    employee_client: EmployeeClient,
    user_client: UserClient,
    leave_client: LeaveClient,
) -> None:
    supervisor_emp_builder = EmployeeBuilder()
    supervisor_emp = employee_client.create(
        first_name=supervisor_emp_builder.first_name, last_name=supervisor_emp_builder.last_name
    )
    supervisor_user_builder = UserBuilder()
    supervisor_user = user_client.create(
        username=supervisor_user_builder.username,
        password=supervisor_user_builder.password,
        user_role_id=ESS_ROLE_ID,
        emp_number=supervisor_emp.emp_number,
    )

    report_emp_builder = EmployeeBuilder()
    report_emp = employee_client.create(
        first_name=report_emp_builder.first_name, last_name=report_emp_builder.last_name
    )
    report_user_builder = UserBuilder()
    report_user = user_client.create(
        username=report_user_builder.username,
        password=report_user_builder.password,
        user_role_id=ESS_ROLE_ID,
        emp_number=report_emp.emp_number,
    )

    employee_client.assign_supervisor(report_emp.emp_number, supervisor_emp_number=supervisor_emp.emp_number)
    leave_client.grant_entitlement(
        emp_number=report_emp.emp_number,
        leave_type_id=ANNUAL_LEAVE_TYPE_ID,
        from_date="2026-01-01",
        to_date="2026-12-31",
        days=10,
    )

    # The report self-applies for leave (API, authenticated as themselves via a real UI login --
    # self-apply lands as "Pending Approval"; an admin assigning leave on someone's behalf instead
    # auto-schedules it with nothing left to approve, confirmed against the running app).
    report_context = browser.new_context(base_url=base_url)
    report_dashboard = (
        LoginPage(report_context.new_page()).open().login(report_user.user_name, report_user_builder.password)
    )
    expect(report_dashboard.heading).to_be_visible()
    report_leave_client = LeaveClient(report_context.request, base_url)
    # Must be a working day (default work week is Mon-Fri) -- a weekend date is rejected with
    # "No Working Days Selected" (hit this for real: 2026-11-21 is a Saturday).
    report_leave_client.apply(
        leave_type_id=ANNUAL_LEAVE_TYPE_ID, from_date="2026-11-23", to_date="2026-11-23"
    )
    report_context.close()

    # The supervisor logs in via the UI and approves it.
    supervisor_context = browser.new_context(base_url=base_url)
    supervisor_page = supervisor_context.new_page()
    supervisor_dashboard = (
        LoginPage(supervisor_page).open().login(supervisor_user.user_name, supervisor_user_builder.password)
    )
    expect(supervisor_dashboard.heading).to_be_visible()

    leave_list = LeaveListPage(supervisor_page).open()
    leave_list.search()
    expect(leave_list.results.row_containing(report_emp_builder.last_name)).to_be_visible()
    leave_list.approve_row(report_emp_builder.last_name)
    expect(supervisor_page.get_by_text("Successfully Updated")).to_be_visible()
    supervisor_context.close()

    employee_client.delete(supervisor_emp.emp_number, report_emp.emp_number)
