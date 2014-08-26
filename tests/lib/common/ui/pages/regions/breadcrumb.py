from selenium.webdriver.common.by import By
from common.ui.pages import PageRegion


class BreadCrumb(PageRegion):
    """
    Describes page breadcrumbs
    """

    _root_locator = (By.CSS_SELECTOR, 'ul.ansible-breadcrumb')
    _item_locator = (By.CSS_SELECTOR, 'a')
    _active_breadcrumb_locator = (By.CSS_SELECTOR, 'ul.ansible-breadcrumb > li.active > a')

    @property
    def active_crumb(self):
        return self.find_element(*self._active_breadcrumb_locator).get_attribute('text')

    @property
    def items(self):
        return dict((el.get_attribute('text'), el) for el in self.find_elements(*self._item_locator))

    def click(self, name):
        if name in self.items:
            self.items[name].click()
        else:
            raise Exception("Breadcrumb named '%s' not found" % name)
