from selenium.webdriver.common.by import By
from common.ui.pages import *

class Main_Menu(Page):
    '''
    '''
    _main_menu_locator = (By.CSS_SELECTOR, '#ansible-main-menu')
    _item_locator = (By.CSS_SELECTOR, 'a')
    _logo_locator = (By.CSS_SELECTOR, '#ansible-brand-logo')
    _item_to_page = {"Home": Dashboard,
                     "Organizations": Organizations_Page,
                     "Users": Users,
                     "Teams": Teams,
                     "Credentials": Credentials,
                     "Projects": Projects,
                     "Inventories": Inventories,
                     "Job Templates": Job_Templates,
                     "Jobs": Jobs}
    _current_item_locator = (By.CSS_SELECTOR, "#ansible-main-menu > li.active > a")

    def __init__(self, testsetup):
        super(Main_Menu, self).__init__(testsetup)
        self._root_element = self.get_visible_element(*self._main_menu_locator)

    def is_displayed(self):
        return self._root_element.is_displayed()

    def current_item(self):
        return self._root_element.find_element(*self._current_item_locator).get_attribute('text')

    @property
    def logo(self):
        return self.selenium.find_element(*self._logo_locator)

    @property
    def items(self):
        return dict((el.get_attribute('text'), el) for el in self._root_element.find_elements(*self._item_locator))

    def click(self, name):
        if name == "Home":
            self.logo.click()
        elif name in self.items:
            self.items[name].click()
        else:
            raise Exception("Main menu item not found: %s" % name)
        # Wait for 'Working...' spinner to appear, and go away
        self._wait_for_results_refresh()
        return self._item_to_page[name](self.testsetup)
