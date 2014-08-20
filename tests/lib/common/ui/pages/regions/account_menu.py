from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import *

class AccountMenu(Page):
    """
    Describes the account menu
    """

    _menu_locator = (By.CSS_SELECTOR, '#account-menu')
    _menu_link_locator = (By.CSS_SELECTOR, '#account-menu-link')
    _submenu_locator = (By.CSS_SELECTOR, '#account-submenu')
    _item_locator = (By.CSS_SELECTOR, '#account-submenu > li > a')

    def __init__(self, testsetup):
        super(AccountMenu, self).__init__(testsetup)
        self._root_element = self.get_visible_element(*self._menu_locator)

    def show(self):
        if not self.is_displayed():
            self._root_element.find_element(*self._menu_link_locator).click()

    def hide(self):
        if self.is_displayed():
            self._root_element.find_element(*self._menu_link_locator).click()

    def is_displayed(self):
        try:
            submenu = self._root_element.find_element(*self._submenu_locator)
        except NoSuchElementException, e:
            return False
        else:
            return submenu.is_displayed()

    @property
    def items(self):
        return dict((el.get_attribute('id'), el) for el in self._root_element.find_elements(*self._item_locator))

    def click(self, name):
        if name in self.items:
            self.items[name].click()
        else:
            raise Exception("Menu item '%s' not found" % name)

    def click_about(self):
        self.click('main_about')
        # TODO: return an About_Dialog object

    def click_view_user(self):
        self.click('main_view_user')
        # TODO: return an User_Page object

    def click_view_license(self):
        self.click('main_view_license')
        # TODO: return an License_Dialog object

    def click_contact_support(self):
        self.click('main_contact_support')

    def click_munin(self):
        self.click('main_munin')

    def click_logout(self):
        self.click('main_logout')
        # TODO: return a Login_Page object
