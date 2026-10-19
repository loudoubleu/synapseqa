import pytest
from playwright.sync_api import Page
from pytest_playwright_visual_snapshot.plugin import AssertSnapshot  # type: ignore[import-untyped]

from framework.ui.pages.login_page import LoginPage


@pytest.mark.ui
def test_login_page_visual_regression(page: Page, assert_snapshot: AssertSnapshot) -> None:
    LoginPage(page).open()
    assert_snapshot(page, name="login_page.png")
