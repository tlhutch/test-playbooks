from selenium.webdriver.common.by import By
from common.ui.pages import PageRegion, Login_Page


class Account_Menu(PageRegion):
    """
    Describes the account menu
    """

    _root_locator = (By.CSS_SELECTOR, '#account-menu')
    _menu_link_locator = (By.CSS_SELECTOR, '#account-menu-link')
    _current_user_locator = (By.CSS_SELECTOR, '#account-menu-link > span.ng-binding')
    _submenu_locator = (By.CSS_SELECTOR, '#account-submenu')
    _item_locator = (By.CSS_SELECTOR, '#account-submenu > li > a')

    def show(self):
        '''Show the account submenu'''
        if self.is_element_not_visible(*self._submenu_locator):
            self.find_element(*self._menu_link_locator).click()

    def hide(self):
        '''Hide the account submenu'''
        if self.is_element_visible(*self._submenu_locator):
            self.find_element(*self._menu_link_locator).click()

    @property
    def current_user(self):
        '''Return the username of the current user'''
        return self.find_element(*self._current_user_locator).text

    @property
    def is_logged_in(self):
        '''Return true if the current page is logged in'''
        return self.find_element(*self._menu_link_locator).is_displayed()

    @property
    def items(self):
        return dict((el.get_attribute('id'), el) for el in self.find_elements(*self._item_locator))

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
        return Login_Page(self.testsetup)
