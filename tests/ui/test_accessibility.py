import pytest
from axe_playwright_python.sync_playwright import Axe  # type: ignore[import-untyped]
from playwright.sync_api import Page

from framework.ui.pages.login_page import LoginPage


@pytest.mark.ui
def test_login_page_has_no_critical_accessibility_violations(page: Page) -> None:
    LoginPage(page).open()
    results = Axe().run(page)

    # The app has known non-critical issues (color-contrast, missing landmarks, …) that
    # are pre-existing and outside this framework's control. This check is deliberately
    # scoped to "critical" impact only, so it's a meaningful regression guard rather than
    # a permanently-failing assertion against debt we can't fix from a test suite.
    critical = [v for v in results.response["violations"] if v["impact"] == "critical"]
    assert critical == [], results.generate_report()
