from common.ui.pages.page import Page
from selenium.webdriver.common.by import By


def input_getter(locator):
    '''
    Generic property fget method
    '''
    def get_field(self):
        return self.get_visible_element(*locator).get_attribute('value')
    return get_field


def input_setter(locator):
    '''
    Generic property fset method
    '''
    def set_field(self, value):
        el = self.get_visible_element(*locator)
        el.clear()
        el.send_keys(value)
    return set_field


class Form_Page(Page):
    '''Describes a basic <form>'''

    # Sub-classes should define locators in the following dictionary
    _locators = {}

    # name = property(base.input_getter(_locators['name']), base.input_setter(_locators['name']))
    # description = property(base.input_getter(_locators['description']), base.input_setter(_locators['description']))

    def click_save(self):
        raise NotImplementedError("Must be implemented by a sub-class")

    def click_reset(self):
        raise NotImplementedError("Must be implemented by a sub-class")
