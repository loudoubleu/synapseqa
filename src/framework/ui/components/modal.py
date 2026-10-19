from playwright.sync_api import Page

from framework.ui.components.component import Component


class Modal(Component):
    """OrangeHRM confirmation dialog (e.g. 'Are you sure?' delete confirmation)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page, page.locator(".oxd-dialog-sheet"))

    def confirm(self, label: str = "Yes, Delete") -> None:
        self.root.get_by_role("button", name=label).click()

    def cancel(self) -> None:
        self.root.get_by_role("button", name="No, Cancel").click()
