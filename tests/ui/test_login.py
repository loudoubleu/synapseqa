import pytest
from playwright.sync_api import Page, expect

from framework.config.settings import Settings
from framework.ui.pages.login_page import LoginPage


@pytest.mark.smoke
@pytest.mark.ui
def test_valid_login_lands_on_dashboard(page: Page, settings: Settings) -> None:
    login_page = LoginPage(page).open()
    dashboard = login_page.login(settings.admin_username, settings.admin_password.get_secret_value())
    expect(dashboard.heading).to_be_visible()


@pytest.mark.ui
def test_invalid_password_shows_error(page: Page, settings: Settings) -> None:
    login_page = LoginPage(page).open()
    login_page.login(settings.admin_username, "not-the-right-password")
    expect(login_page.invalid_credentials_message).to_be_visible()


@pytest.mark.ui
def test_empty_fields_show_required_validation(page: Page) -> None:
    login_page = LoginPage(page).open()
    login_page.submit.click()
    expect(login_page.required_messages).to_have_count(2)
