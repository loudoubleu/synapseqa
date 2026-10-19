from playwright.sync_api import Locator

from framework.ui.components.component import Component


class DataTable(Component):
    """OrangeHRM result grid: root scopes to the table body, one '.oxd-table-card' per row."""

    def rows(self) -> Locator:
        return self.root.locator(".oxd-table-card")

    def row_containing(self, text: str) -> Locator:
        return self.root.locator(".oxd-table-card", has_text=text)
