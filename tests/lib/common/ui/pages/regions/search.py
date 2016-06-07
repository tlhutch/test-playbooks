from selenium.webdriver.common.by import By

from common.ui.pages.page import Region
from common.ui.pages.regions import Clickable


class SearchValueInput(Region):
    _root_extension = (By.CSS_SELECTOR, '#search_value_input')


class SearchResetButton(Clickable):
    _spinny = True
    _root_extension = (By.CSS_SELECTOR, '#search-reset-button')


class SearchButton(Clickable):
    _spinny = True
    _root_extension = (By.CSS_SELECTOR, '#search-submit-button')


class Search(Region):
    _root_extension = (By.CSS_SELECTOR, '.TagSearch-bar')

    @property
    def search_button(self):
        return SearchButton(self.page, root=self.root)

    @property
    def reset_button(self):
        return SearchResetButton(self.page, root=self.root)

    @property
    def value_input(self):
        return SearchValueInput(self.page, root=self.root)

    def __call__(self, value):
        if self.reset_button.is_displayed():
            self.reset_button.click()
            self.reset_button.wait_until_not_displayed()
        self.value_input.root.send_keys(value)
        self.search_button.click()
