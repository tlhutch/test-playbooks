from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import PageRegion
from common.ui.pages.forms import input_getter, input_setter, Form_Page
from common.ui.pages.regions.buttons import Base_Button


class Search_Region(PageRegion):
    '''Represents the search filter region'''
    _root_locator = (By.CSS_SELECTOR, "#search-widget-container")

    # Drop-down list
    _search_type_locator = (By.CSS_SELECTOR, "#search_field_ddown")
    _search_type_lookup_locator = (By.CSS_SELECTOR, "#organizationSearchDropdown")

    # Textbox
    _search_value_locator = (By.CSS_SELECTOR, "#search_value_input")
    search_value = property(input_getter(_search_value_locator), input_setter(_search_value_locator))

    # Buttons
    _search_btn_locator = (By.CSS_SELECTOR, "a.search-reset-start > i.fa-search")  # TODO: change to #search-submit-button
    _reset_btn_locator = (By.CSS_SELECTOR, "a.search-reset-start > i.fa-times")  # TODO: change to #search-reset-button

    @property
    def search_type_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._search_type_locator), _item_class=self._item_class)

    @property
    def search_type_options(self):
        return Search_Type_Options(self.testsetup, _root_element=self.find_element(*self._search_type_lookup_locator))

    @property
    def search_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._search_btn_locator), _item_class=self._item_class)

    @property
    def reset_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._reset_btn_locator), _item_class=self._item_class)


class Search_Type_Options(PageRegion):
    '''Describes the search type options region'''

    _root_locator = (By.CSS_SELECTOR, "#organizationSearchDropdown")
    _item_locator = (By.CSS_SELECTOR, "a")
    _selected_option_locator = (By.CSS_SELECTOR, '#search_field_ddown > span')

    @property
    def selected_item(self):
        return self.find_element(*self._selected_option_locator).get_attribute('text')

    def get(self, name):
        for el in self.items():
            if el.get_attribute('text') == name:
                return el
        raise Exception("Select option named '%s' not found" % name)

    def items(self):
        return self.find_elements(*self._item_locator)
