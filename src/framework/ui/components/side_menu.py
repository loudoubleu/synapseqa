from playwright.sync_api import Page

from framework.ui.components.component import Component


class SideMenu(Component):
    def __init__(self, page: Page) -> None:
        super().__init__(page, page.locator(".oxd-main-menu"))

    def item_names(self) -> set[str]:
        return set(self.root.locator(".oxd-main-menu-item").all_text_contents())
