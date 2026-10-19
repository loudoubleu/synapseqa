import pytest
from playwright.sync_api import Page, expect

from framework.api.clients.user_client import ESS_ROLE_ID, UserClient
from framework.api.models.employee import Employee
from framework.data.builders import UserBuilder
from framework.ui.pages.admin.user_management_page import UserManagementPage


@pytest.mark.e2e
@pytest.mark.destructive
def test_user_created_via_api_is_listed_in_admin_search(
    admin_page: Page, employee: Employee, user_client: UserClient
) -> None:
    builder = UserBuilder()
    created = user_client.create(
        username=builder.username,
        password=builder.password,
        user_role_id=ESS_ROLE_ID,
        emp_number=employee.emp_number,
        status=builder.status,
    )

    user_mgmt = UserManagementPage(admin_page).open()
    user_mgmt.username.fill(created.user_name)
    user_mgmt.search()

    expect(user_mgmt.results.row_containing(created.user_name)).to_be_visible()

    user_client.delete(created.id)
