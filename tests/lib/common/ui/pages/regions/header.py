from common.ui.pages import Page
from common.ui.pages.regions.account_menu import AccountMenu
from selenium.webdriver.common.by import By

class HeaderRegion(Page):
    # LoggedIn
    _menu_logout_link_locator = (By.ID, "main_logout")
    _logout_link_locator = (By.ID, "main_logout")
    _user_indicator_locator = (By.ID, "main_view_user")
    _account_menu_locator = (By.ID, "account-menu-link")
    _site_navigation_menus_locator = (By.CSS_SELECTOR, "#ansible-main-menu > li")
    _account_submenu_locator = (By.CSS_SELECTOR, "#account-submenu > li > a")

    @property
    def is_logged_in(self):
        return self.is_element_visible(*self._account_menu_locator)

    def logout(self):
        self.account_menu.show()
        self.account_menu.click('main_logout')
        from login import LoginPage
        return LoginPage(self.testsetup)

    def site_navigation_menu(self, value):
        # used to access on specific menu
        for menu in self.site_navigation_menus:
            if menu.name == value:
                return menu
        raise Exception("Menu not found: '%s'. Menus: %s" % (value, [menu.name for menu in self.site_navigation_menus]))

    @property
    def site_navigation_menus(self):
        # returns a list containing all the site navigation menus
        from regions.header_menu import HeaderMenu
        return [HeaderMenu(self.testsetup, web_element) for web_element in self.selenium.find_elements(*self._site_navigation_menus_locator)]

    @property
    def account_menu(self):
        # returns a dictionary containing all the account menu links
        return AccountMenu(self.testsetup)
