from common.ui.pages import Page
from common.ui.pages.regions.main_menu import MainMenu
from common.ui.pages.regions.account_menu import AccountMenu
from selenium.webdriver.common.by import By

class HeaderRegion(Page):

    @property
    def is_logged_in(self):
        # _account_menu_locator = (By.ID, "account-menu-link")
        # return self.is_element_visible(*_account_menu_locator)
        return AccountMenu(self.testsetup).is_logged_in

    def logout(self):
        self.account_menu.show()
        self.account_menu.click('main_logout')
        from login import LoginPage
        return LoginPage(self.testsetup)

    @property
    def main_menu(self):
        return MainMenu(self.testsetup)

    @property
    def account_menu(self):
        return AccountMenu(self.testsetup)
