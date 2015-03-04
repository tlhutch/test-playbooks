from selenium.webdriver.common.by import By
from common.ui.pages import PageRegion
from common.ui.pages.regions.main_menu import Main_Menu
from common.ui.pages.regions.account_menu import Account_Menu
from common.ui.pages.regions.mobile_menu import Mobile_Menu


class Header_Region(PageRegion):
    _root_locator = (By.ID, 'main-menu-container')

    @property
    def mobile_menu(self):
        return Mobile_Menu(self.testsetup)

    @property
    def account_menu(self):
        return Account_Menu(self.testsetup)

    @property
    def main_menu(self):
        return Main_Menu(self.testsetup)

    @property
    def current_menu(self):
        if self.account_menu.is_displayed():
            return self.account_menu
        elif self.mobile_menu.is_displayed():
            return self.mobile_menu
        else:
            raise Exception("Unable to determine if logged in")

    @property
    def is_logged_in(self):
        '''
        Determine which menu is visible, and route to the appropriate property.
        '''
        return self.current_menu.is_logged_in

    @property
    def current_user(self):
        '''
        Determine which menu is visible, and route to the appropriate property.
        '''
        return self.current_menu.current_user

    def logout(self):
        '''
        Logout by clicking 'Logout' in the appropriate menu.
        '''
        return self.current_menu.click("Logout")
