from selenium.webdriver.common.by import By
from common.ui.pages import PageRegion, Login_Page, Portal_Page, Dashboard_Page, User_Edit_Page
from common.ui.pages.regions.lists import List_Region


class Account_Menu(PageRegion):
    """
    Describes the account menu region.
    """
    _root_locator = (By.CSS_SELECTOR, '#account-menu')
    _menu_link_locator = (By.CSS_SELECTOR, '#account-menu-link')
    _current_user_locator = (By.CSS_SELECTOR, '#account-menu-link > span')

    @property
    def submenu(self):
        return Account_Submenu(self.testsetup)

    @property
    def current_user(self):
        '''Return the username of the current user'''
        return self.find_element(*self._current_user_locator).text

    @property
    def is_logged_in(self):
        '''
        Return true if the current page is logged in.
        '''
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
            self.wait_for_visible()

    def hide(self):
        '''Hide the account submenu'''
        if self.submenu.is_displayed():
            self.find_element(*self._menu_link_locator).click()
            self.wait_for_not_visible()

    def click(self, name):
        '''
        Issue a click event on the provided submenu item.
        '''
        self.show()
        return self.submenu.click(name)


class Account_Submenu(List_Region):
    _root_locator = (By.CSS_SELECTOR, '#account-submenu.dropdown-menu')
    _related = {
        'About Tower': None,  # FIXME
        'Account Settings': User_Edit_Page,
        'Contact Support': None,  # FIXME
        'Inventory Script': None,  # FIXME
        'Management Jobs': None,  # FIXME
        'Monitor Tower': None,  # FIXME
        'Portal Mode': Portal_Page,
        'Exit Portal': Dashboard_Page,
        'View License': None,  # FIXME
        'Logout': Login_Page,
    }
