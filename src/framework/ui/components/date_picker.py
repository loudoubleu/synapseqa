from framework.ui.components.component import Component


class DatePicker(Component):
    """OrangeHRM date field: root is the text input, accepts direct yyyy-mm-dd entry."""

    def set_date(self, value: str) -> None:
        self.root.fill(value)
        self.page.keyboard.press("Escape")
