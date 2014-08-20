from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import *

class BreadCrumb(Page):
    """
    Describes page breadcrumbs
    """

    _breadcrumb_locator = (By.CSS_SELECTOR, '#ansible-breadcrumb')
    _item_locator = (By.CSS_SELECTOR, 'a')
    _active_breadcrumb_locator = (By.CSS_SELECTOR, '#ansible-breadcrumb > li.active > a')

    def __init__(self, testsetup):
        super(AccountMenu, self).__init__(testsetup)
        self._root_element = self.get_visible_element(*self._breadcrumb_locator)

    def is_displayed(self):
        return self._root_element.is_displayed()

    def current_item(self):
        return self._root_element.find_element(*self._active_breadcrumb_locator).get_attribute('text')

    @property
    def items(self):
        return dict((el.get_attribute('id'), el) for el in self._root_element.find_elements(*self._item_locator))

    def click(self, name):
        if name in self.items:
            self.items[name].click()
        else:
            raise Exception("Breadcrumb named '%s' not found" % name)
