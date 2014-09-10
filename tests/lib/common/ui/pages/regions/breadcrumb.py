from selenium.webdriver.common.by import By
from common.ui.pages.regions.lists import List_Region


class Breadcrumb_Region(List_Region):
    '''Describes the breadcrumb region'''

    _root_locator = (By.CSS_SELECTOR, 'ul.ansible-breadcrumb')
    _item_locator = (By.CSS_SELECTOR, 'a')
    _active_breadcrumb_locator = (By.CSS_SELECTOR, 'ul.ansible-breadcrumb > li.active > a')

    @property
    def active_crumb(self):
        return self.find_element(*self._active_breadcrumb_locator).get_attribute('text')
