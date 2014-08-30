from selenium.webdriver.common.by import By
from common.ui.pages import PageRegion


class Breadcrumb_Region(PageRegion):
    '''Describes the breadcrumb region'''

    _root_locator = (By.CSS_SELECTOR, 'ul.ansible-breadcrumb')
    _item_locator = (By.CSS_SELECTOR, 'a')
    _active_breadcrumb_locator = (By.CSS_SELECTOR, 'ul.ansible-breadcrumb > li.active > a')

    @property
    def active_crumb(self):
        return self.find_element(*self._active_breadcrumb_locator).get_attribute('text')

    def get(self, name):
        for el in self.items():
            if el.get_attribute('text') == name:
                return el
        raise Exception("Breadcrumb named '%s' not found" % name)

    def items(self):
        return self.find_elements(*self._item_locator)
