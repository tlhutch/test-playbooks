from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import PageRegion
from common.ui.pages.forms import input_getter, input_setter, Form_Page
from common.ui.pages.regions.buttons import Base_Button, Search_Button, Reset_Button
from common.ui.pages.regions.lists import List_Region


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
    def search_type(self):
        return Search_DropDown(self.testsetup,
                               _item_class=self._item_class,
                               _root_element=self.find_element(*self._search_type_locator),
                               _options_element=self.find_element(*self._search_type_lookup_locator))

    @property
    def search_btn(self):
        return Search_Button(self.testsetup, _root_element=self.find_element(*self._search_btn_locator), _item_class=self._item_class)

    @property
    def reset_btn(self):
        return Reset_Button(self.testsetup, _root_element=self.find_element(*self._reset_btn_locator), _item_class=self._item_class)


class Search_DropDown(PageRegion):
    '''Describes the search type options region'''
    _root_element = None
    _options_element = None

    @property
    def option_btn(self):
        '''Return a the currently selected option text'''
        return Base_Button(self.testsetup, _root_element=self._root_element, _item_class=self._item_class)

    @property
    def selected_option(self):
        '''Return a the currently selected option text'''
        return self._root_element.text

    @property
    def options(self):
        '''Return a List_Region object representing available options'''
        return List_Region(self.testsetup, _root_element=self._options_element)

    def select(self, name):
        # Open the options menu
        if not self.options.is_displayed():
            self.option_btn.click()
        # Click the desired option
        self.options.get(name).click()
        # Assert the right thing happened
        assert name == self.selected_option, \
            "Expected selected option: %s. Actual selected option: %s" % \
            (name, self.selected_option)
