from framework.ui.components.component import Component


class Autocomplete(Component):
    """OrangeHRM typeahead input ('Type for hints...'): root is the text input itself."""

    def search_and_select(self, query: str, option: str) -> None:
        self.root.fill(query)
        self.page.get_by_role("option", name=option).click()
