from selenium.webdriver.common.by import By
from common.ui.pages import BaseRegion, Login_Page, User_Edit_Page
from common.ui.pages.regions.lists import List_Region


class Account_Menu(BaseRegion):
    """
    Describes the account menu
    """
    _root_locator = (By.CSS_SELECTOR, '#account-menu')
    _menu_link_locator = (By.CSS_SELECTOR, '#account-menu-link')
    _current_user_locator = (By.CSS_SELECTOR, '#account-menu-link > span')
    _submenu_locator = (By.CSS_SELECTOR, '#account-submenu')
    _related = {
        'About Tower': 'FIXME',
        'Account Settings': 'User_Edit_Page',
        'View License': 'FIXME',
        'Contact Support': 'FIXME',
        'Monitor Tower': 'FIXME',
        'Logout': 'Login_Page',
    }

    @property
    def submenu(self):
        return List_Region(self.testsetup, _root_element=self.find_element(*self._submenu_locator))

    @property
    def current_user(self):
        '''Return the username of the current user'''
        return self.find_element(*self._current_user_locator).text

    @property
    def is_logged_in(self):
        '''Return true if the current page is logged in'''
        return self.find_element(*self._menu_link_locator).is_displayed()

    def keys(self):
        '''Return submenu keys'''
        return self.submenu.keys()

    def items(self):
        '''Return submenu items'''
        return self.submenu.items()

    def show(self):
        '''Show the account submenu'''
        if not self.submenu.is_displayed():
            self.find_element(*self._menu_link_locator).click()

    def hide(self):
        '''Hide the account submenu'''
        if self.submenu.is_displayed():
            self.find_element(*self._menu_link_locator).click()

    def click(self, name):
        '''
        Issue a click event on the provided submenu item.
        '''
        self.show()
        self.submenu.get(name).click()
        self.wait_for_spinny()
        return self.get_related(name)(self.testsetup)
