from selenium.webdriver.common.by import By
from common.ui.pages import *


class Main_Menu(PageRegion):
    '''
    '''
    _root_locator = (By.CSS_SELECTOR, '#ansible-main-menu')
    _item_locator = (By.CSS_SELECTOR, 'a')
    _logo_locator = (By.CSS_SELECTOR, '#ansible-brand-logo')
    _item_to_page = {"Home": Dashboard_Page,
                     "Organizations": Organizations_Page,
                     "Users": Users,
                     "Teams": Teams,
                     "Credentials": Credentials,
                     "Projects": Projects,
                     "Inventories": Inventories,
                     "Job Templates": Job_Templates,
                     "Jobs": Jobs}
    _active_item_locator = (By.CSS_SELECTOR, "#ansible-main-menu > li.active > a")

    @property
    def active_item(self):
        return self.find_element(*self._active_item_locator).get_attribute('text')

    @property
    def logo(self):
        return self.selenium.find_element(*self._logo_locator)

    @property
    def items(self):
        return dict((el.get_attribute('text'), el) for el in self.find_elements(*self._item_locator))

    def click(self, name):
        if name == "Home":
            self.logo.click()
        elif name in self.items:
            self.items[name].click()
        else:
            raise Exception("Main menu item not found: %s" % name)
        # Wait for 'Working...' spinner to appear, and go away
        self.wait_for_spinny()
        return self._item_to_page[name](self.testsetup)
