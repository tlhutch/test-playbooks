from selenium.webdriver.common.by import By
from common.ui.pages import *
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
    def is_logged_in(self):
        if self.account_menu.is_displayed():
            return self.account_menu.is_logged_in
        elif self.mobile_menu.is_displayed():
            return self.mobile_menu.is_logged_in
        else:
            raise Exception("Unable to determine if logged in")

    def logout(self):
        if self.account_menu.is_displayed():
            return self.account_menu.click("Logout")
        elif self.mobile_menu.is_displayed():
            return self.mobile_menu.click("Logout")
        else:
            raise Exception("Unable to locate account menu, or mobile menu.")
