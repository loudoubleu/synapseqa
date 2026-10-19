from playwright.sync_api import Page

from framework.ui.pages.base_page import BasePage


class DashboardPage(BasePage):
    path = "/web/index.php/dashboard/index"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Dashboard")
