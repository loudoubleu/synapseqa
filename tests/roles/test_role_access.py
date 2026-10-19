from pathlib import Path

import pytest
from playwright.sync_api import Page, Playwright, expect

from framework.auth.roles import EXPECTED_MENU, Role
from framework.ui.components.side_menu import SideMenu


@pytest.mark.roles
@pytest.mark.parametrize("role", [Role.ADMIN, Role.ESS], indirect=True)
def test_main_menu_matches_role(logged_in_as: Page, role: Role) -> None:
    menu = SideMenu(logged_in_as).item_names()
    assert EXPECTED_MENU[role] <= menu
    if role is Role.ESS:
        assert "Admin" not in menu


@pytest.mark.roles
def test_ess_user_cannot_open_admin_page(ess_page: Page) -> None:
    ess_page.goto("/web/index.php/admin/viewSystemUsers")
    expect(ess_page.get_by_text("Credential Required")).to_be_visible()


@pytest.mark.roles
@pytest.mark.api
def test_ess_user_blocked_from_admin_api(
    playwright: Playwright, ess_storage_state: Path, base_url: str
) -> None:
    request_context = playwright.request.new_context(base_url=base_url, storage_state=ess_storage_state)
    response = request_context.get("/web/index.php/api/v2/admin/users", params={"limit": 1})
    assert response.status == 403
    request_context.dispose()
