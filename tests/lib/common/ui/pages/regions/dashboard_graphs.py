from selenium.webdriver.common.by import By

from common.ui.pages.page import Region
from clickable import Clickable


class DashboardGraphStatus(Clickable):

    @property
    def text(self):
        return self.text.lower()

    @property
    def background_color(self):
        return self.root.value_of_css_property('background-color')

    def is_enabled(self):
        return self.background_color == 'rgba(215, 215, 215, 1)'
        
    def is_disabled(self):
        return not self.is_enabled()

    def wait_until_enabled(self):
        self.wait.until(lambda _: self.is_enabled())

    def wait_until_disabled(self):
        self.wait.until(lambda _: self.is_disabled())


class DashboardGraphToggle(DashboardGraphStatus):

    def enable(self):
        if self.is_disabled():
            self.click()
            self.wait_until_enabled()

        return self.page

    def disable(self):
        if self.is_enabled():
            self.click()
            self.wait_until_disabled()

        return self.page


class DashboardGraphTab(DashboardGraphStatus):

    def click(self):
        super(DashboardGraphTab, self).click()
        
        self.wait_until_enabled()

        return self.page


class DashboardGraphDropdown(Clickable):

    _item_locator = None 

    @property
    def item_locator(self):
        return self.kwargs.get('item_locator', self._item_locator)

    def _items(self):
        for element in self.page.find_elements(self.item_locator):
            yield Clickable(self.page, root=element)

    def _collapse(self):
        item = next(self._items())

        if item.is_displayed():
            self.click()
            item.wait_until_not_displayed()

    def _expand(self):
        item = next(self._items())

        if not item.is_displayed():
            self.click()
            item.wait_until_displayed()

    def get_options(self):
        self._expand()

        options = []

        for item in self._items():
            options.append(item.root.text.lower())

        self._collapse()

        return options

    def select_option(self, text):
        text = text.lower()

        self._expand()

        for item in self._items():
            if item.root.text.lower() == text:
                item.click()
                self._collapse()
                return

        self._collapse()

        raise NoSuchElementException
