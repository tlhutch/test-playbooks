from operator import sub
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from common.ui.pages import PageRegion, Login_Page, User_Edit_Page, Portal_Page, Dashboard_Page
from common.ui.pages.regions.lists import List_Region
from common.ui.pages.regions.buttons import Base_Button
from common.ui.pages.regions.main_menu import Main_Menu
from common.ui.pages.regions.account_menu import Account_Submenu


class Mobile_Submenu(List_Region):
    """
    Describes the mobile menu region
    """
    _root_locator = (By.CSS_SELECTOR, '#ansible-mobile-menu')
    _related = dict(Main_Menu._related, **Account_Submenu._related)


class Mobile_Menu(PageRegion):
    """
    Describes the mobile menu region
    """
    _root_locator = (By.CSS_SELECTOR, '#main-menu-toggle-button')
    _menu_btn_locator = (By.CSS_SELECTOR, '#main-menu-toggle-button')

    @property
    def is_logged_in(self):
        '''
        Return true if the current page is logged in.
        '''
        return self.menu_btn.is_displayed()

    @property
    def menu_btn(self):
        '''
        Return the element representing the main menu toggle button
        '''
        return Base_Button(self.testsetup, _root_locator=self._menu_btn_locator)

    @property
    def submenu(self):
        '''
        Return a List_Region corresponding to the mobile menu.
        '''
        return Mobile_Submenu(self.testsetup)

    def show(self):
        '''Show the mobile menu'''
        if not self.submenu.is_displayed():
            self._root_element.click()

    def hide(self):
        '''
        Hide the mobile menu by clicking -200 px from the menu.
        '''
        if self.submenu.is_displayed():
            current_location = (self._root_element.location['x'], self._root_element.location['y'])
            new_location = map(sub, current_location, (200, 0))
            ActionChains(self.selenium).move_by_offset(*new_location).click().perform()

    def keys(self):
        '''Return submenu keys'''
        return self.submenu.keys()

    def items(self):
        '''Return submenu items'''
        return self.submenu.items()

    def click(self, name):
        '''
        Issue a click event on the provided submenu item.
        '''
        self.show()
        return self.submenu.click(name)
