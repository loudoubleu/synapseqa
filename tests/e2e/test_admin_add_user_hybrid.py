import pytest
from playwright.sync_api import Page, expect

from framework.api.clients.user_client import UserClient
from framework.api.models.employee import Employee
from framework.data.builders import UserBuilder
from framework.ui.components.toast import Toast
from framework.ui.pages.admin.user_management_page import UserManagementPage


@pytest.mark.e2e
@pytest.mark.destructive
def test_admin_creates_user_via_ui_for_api_created_employee(
    admin_page: Page, employee: Employee, user_client: UserClient
) -> None:
    builder = UserBuilder()
    user_mgmt = UserManagementPage(admin_page).open()
    add_user = user_mgmt.open_add_user()
    add_user.user_role.choose("ESS")
    add_user.employee_name.search_and_select(employee.last_name, employee.last_name)
    add_user.status.choose("Enabled")
    add_user.username.fill(builder.username)
    add_user.password.fill(builder.password)
    add_user.confirm_password.fill(builder.password)
    add_user.save()

    toast = Toast(admin_page)
    expect(toast.root).to_be_visible()
    assert "Successfully Saved" in toast.message

    users = user_client.list_all(limit=50)
    matching = [u for u in users.data if u.user_name == builder.username]
    assert matching
    user_client.delete(matching[0].id)
