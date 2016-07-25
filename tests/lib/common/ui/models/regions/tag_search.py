import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from common.ui.page import Region

__all__ = ['TagSearch']


class TagSearch(Region):

    _search_button = (By.CLASS_NAME, 'TagSearch-searchButton')
    _search_input = (By.CLASS_NAME, 'TagSearch-searchTermInput')
    _type_dropdown = (By.CLASS_NAME, 'TagSearch-typeDropdown')

    @property
    def search_button(self):
        return self.find_element(*self._search_button)

    @property
    def search_input(self):
        return self.find_element(*self._search_input)

    @property
    def search_type_dropdown(self):
        self.wait.until(lambda _: self.is_element_displayed(*self._type_dropdown))
        element = self.find_element(*self._type_dropdown)
        return SearchTypeDropdown(self.page, root=element)

    def add_filter(self, search_type, value):
        self.search_type_dropdown.set_value(search_type)
        search_input = self.search_input
        search_input.clear()
        search_input.send_keys(value)
        self.search_button.click()
        time.sleep(3)


class SearchTypeDropdown(Region):

    _click_to_close = (By.CLASS_NAME, 'TagSearch-clickToClose')
    _items = (By.CLASS_NAME, 'TagSearch-dropdownItem')

    def _collapse(self):
        if self.page.is_element_displayed(*self._click_to_close):
            self.page.find_element(*self._click_to_close).click()

    def _expand(self):
        if not self.page.is_element_displayed(*self._click_to_close):
            self.root.click()

    @property
    def options(self):
        self._expand()
        elements = self.find_elements(*self._items)
        options = [e.text.lower() for e in elements if e.text]
        self._collapse()
        return options

    def get_value(self):
        return self.root.text.lower()

    def set_value(self, text):
        search_text = text.lower()
        self._expand()
        for element in self.find_elements(*self._items):
            if element.text and element.text.lower() == search_text:
                element.click()
                self._collapse()
                return
        self._collapse()
        raise NoSuchElementException
