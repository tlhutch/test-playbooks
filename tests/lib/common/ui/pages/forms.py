from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from common.ui.pages.page import Page


def input_getter(locator):
    '''
    Generic property fget method
    '''
    def get_field(self):
        return self.find_visible_element(*locator).get_attribute('value')
    return get_field


def input_setter(locator):
    '''
    Generic property fset method
    '''
    def set_field(self, value):
        el = self.find_visible_element(*locator)
        el.clear()
        el.send_keys(value)
    return set_field


class Form_Page(Page):
    '''Object that defines various helpers for interacting with browser <form>s'''

    # Sub-classes should define locators in the following dictionary
    _locators = {}

    # name = property(base.input_getter(_locators['name']), base.input_setter(_locators['name']))
    # description = property(base.input_getter(_locators['description']), base.input_setter(_locators['description']))

    def click_save(self):
        raise NotImplementedError("Must be implemented by a sub-class")

    def click_reset(self):
        raise NotImplementedError("Must be implemented by a sub-class")

    def fill_field_element_with_wait(self, data, field_element):
        field_element = self.fill_field_element(data, field_element)
        # Stupid wait for ajax interval
        time.sleep(2)
        return field_element

    def fill_field_element_clears_text(self, data, field_element):
        '''Fill field with workaround for javascript clearing behavior'''
        field_element.click()
        time.sleep(1)
        field_element.clear()
        field_element.send_keys(data)

    def fill_field_element(self, data, field_element):
        field_element.clear()
        field_element.send_keys(data)
        return field_element

    def fill_field_by_locator(self, data, *locator):
        field_element = self._selenium_root.find_element(*locator)
        self.fill_field_element(data, field_element)
        return field_element

    def fill_field_by_locator_with_wait(self, data, *locator):
        field_element = self._selenium_root.find_element(*locator)
        self.fill_field_element_with_wait(data, field_element)
        return field_element

    def select_dropdown(self, value, *element):
        select = Select(self._selenium_root.find_element(*element))
        select.select_by_visible_text(value)

    def select_dropdown_by_value(self, value, *element):
        select = Select(self._selenium_root.find_element(*element))
        select.select_by_value(value)
