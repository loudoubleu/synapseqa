from framework.ui.components.component import Component


class DatePicker(Component):
    """OrangeHRM date field: root is the text input, accepts direct yyyy-mm-dd entry.

    Uses an explicit select-all + delete + type rather than .fill() -- on some of these fields
    (confirmed on Leave > Apply's To Date, not just a one-off), .fill() doesn't clear existing
    content first and leaves the new value concatenated onto the old one instead of replacing it.
    """

    def set_date(self, value: str) -> None:
        self.root.click()
        self.root.press("Control+A")
        self.root.press("Delete")
        self.root.type(value, delay=30)
        self.page.keyboard.press("Escape")
