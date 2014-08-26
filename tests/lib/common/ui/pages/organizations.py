from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import *
from common.ui.pages.forms import input_getter, input_setter, Form_Page
from common.ui.pages.regions.stream_container import Activity_Stream_Region


class Organizations_Page(Base):
    '''FIXME'''
    _tab_title = "Organizations"
    _add_btn_locator = (By.CSS_SELECTOR, '#add_btn')
    _activity_stream_btn_locator = (By.CSS_SELECTOR, '#stream_btn')

    # Search form
    _search_widget_locator = (By.CSS_SELECTOR, '#search-widget-container')
    _search_select_locator = (By.CSS_SELECTOR, '#search-field-ddown')
    _search_value_locator = (By.CSS_SELECTOR, '#search-value-input')

    # Results table
    _table_locator = (By.CSS_SELECTOR, '#organizations_table')

    @property
    def add_button(self):
        return self.find_visible_element(*self._add_btn_locator)

    @property
    def has_add_button(self):
        try:
            return self.add_button.is_displayed()
        except NoSuchElementException:
            return False

    def click_add(self):
        self.add_button.click()
        return Organization_Create_Page(self.testsetup)

    @property
    def activity_stream_button(self):
        return self.find_visible_element(*self._activity_stream_btn_locator)

    @property
    def has_activity_stream_button(self):
        try:
            return self.activity_stream_button.is_displayed()
        except NoSuchElementException:
            return False

    def click_activity_stream(self):
        self.activity_stream_button.click()
        obj = Organizations_Activity_Page(self.testsetup)
        obj.wait_for_slidein()
        return obj


class Organizations_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all organizations'''
    _tab_title = "Organizations"
    _parent_object = Organizations_Page


class Organization_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Organizations"


class Organization_Create_Page(Base):
    '''Describes the organization edit page'''

    _tab_title = "Organizations"
    _breadcrumb_title = 'Create Organization'
    _locators = {
        'name': (By.CSS_SELECTOR, '#organization_name'),
        'description': (By.CSS_SELECTOR, '#organization_description')
    }
    _save_btn_locator = (By.CSS_SELECTOR, '#organization_save_btn')
    _reset_btn_locator = (By.CSS_SELECTOR, '#organization_reset_btn')

    name = property(input_getter(_locators['name']), input_setter(_locators['name']))
    description = property(input_getter(_locators['description']), input_setter(_locators['description']))

    def click_save(self):
        self.find_visible_element(*self._save_btn_locator).click()
        return Organizations_Page(self.testsetup)

    def click_reset(self):
        self.find_visible_element(*self._reset_btn_locator).click()
        return Organizations_Page(self.testsetup)
