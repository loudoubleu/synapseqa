from playwright.sync_api import Page

from framework.ui.components.component import Component


class Toast(Component):
    """OrangeHRM success/error banner (no ARIA role; CSS-class-scoped by necessity)."""

    def __init__(self, page: Page) -> None:
        super().__init__(page, page.locator(".oxd-toast"))

    @property
    def message(self) -> str:
        return self.root.inner_text()
