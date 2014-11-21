from selenium.webdriver.common.by import By
from common.ui.pages import *
from common.ui.pages.regions.main_menu import Main_Menu
from common.ui.pages.regions.account_menu import Account_Menu


class HeaderRegion(PageRegion):
    _root_locator = (By.ID, 'main-menu-container')

    @property
    def account_menu(self):
        return Account_Menu(self.testsetup)

    @property
    def main_menu(self):
        return Main_Menu(self.testsetup)

    @property
    def is_logged_in(self):
        return self.account_menu.is_logged_in

    def logout(self):
        self.account_menu.show()
        self.account_menu.click('main_logout')
        from common.ui.pages.login import Login_Page
        return Login_Page(self.testsetup)
