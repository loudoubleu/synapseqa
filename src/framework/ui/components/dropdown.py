from framework.ui.components.component import Component


class Dropdown(Component):
    """OrangeHRM custom select (not a native <select>): a div trigger + role=listbox options."""

    def choose(self, option: str) -> None:
        self.root.click()
        self.page.get_by_role("option", name=option).click()
