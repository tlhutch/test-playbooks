import base
import forms
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class Organizations_Page(base.Base):
    '''FIXME'''
    _tab_title = "Organizations"
    _add_button_locator = (By.CSS_SELECTOR, '#add_btn')
    _search_widget_locator = (By.CSS_SELECTOR, '#search-widget-container')
    _activity_stream_button_locator = (By.CSS_SELECTOR, '#stream_btn')

    @property
    def add_button(self):
        return self.get_visible_element(*self._add_button_locator)

    @property
    def has_add_button(self):
        try:
            return self.add_button.is_displayed()
        except NoSuchElementException:
            return False

    def click_add(self):
        self.add_button.click()
        return Organization_Edit_Page(self.testsetup)

    @property
    def activity_stream_button(self):
        return self.get_visible_element(*self._activity_stream_button_locator)

    @property
    def has_activity_stream_button(self):
        try:
            return self.activity_stream_button.is_displayed()
        except NoSuchElementException:
            return False

    def click_activity_stream(self):
        self.activity_stream_button.click()
        return Organization_Activity_Page(self.testsetup)


class Organization_Activity_Page(base.Base):
    '''fixme'''


class Organization_Edit_Page(forms.Form_Page):
    '''Describes the organization edit page'''

    _breadcrumb_title = 'Create Organization'
    _locators = {
        'name': (By.CSS_SELECTOR, '#organization_name'),
        'description': (By.CSS_SELECTOR, '#organization_description')
    }
    _save_btn_locator = (By.CSS_SELECTOR, '#organization_save_btn')
    _reset_btn_locator = (By.CSS_SELECTOR, '#organization_reset_btn')

    name = property(forms.input_getter(_locators['name']), forms.input_setter(_locators['name']))
    description = property(forms.input_getter(_locators['description']), forms.input_setter(_locators['description']))

    def click_save(self):
        self.get_visible_element(*self._save_btn_locator).click()
        return Organizations_Page(self.testsetup)

    def click_reset(self):
        self.get_visible_element(*self._reset_btn_locator).click()
        return Organizations_Page(self.testsetup)
