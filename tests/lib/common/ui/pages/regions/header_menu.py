from common.ui.pages import *
#from common.ui.pages.page import Page
#from common.ui.pages.dashboard import Dashboard
#from common.ui.pages.organizations import Organizations
#from common.ui.pages.users import Users
#from common.ui.pages.teams import Teams
#from common.ui.pages.credentials import Credentials
#from common.ui.pages.projects import Projects
#from common.ui.pages.inventories import Inventories
#from common.ui.pages.job_templates import Job_Templates
#from common.ui.pages.jobs import Jobs

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

class HeaderMenu(Page):
    """
    This class accesses the header area from the top-level Page.
    To access:
        HeaderMenu(self.testsetup, element_lookup)
    Where element_lookup is:
        * the web element of the menu you want
    Example:
        HeaderMenu(self.testsetup, infrastructure_element) returns the Infrastructure menu
    """

    _menu_items_locator = (By.ID, 'main_tabs')
    _name_locator = (By.CSS_SELECTOR, 'a')
    _item_page = {"Home": Dashboard,
                  "Organizations": Organizations,
                  "Users": Users,
                  "Teams": Teams,
                  "Credentials": Credentials,
                  "Projects": Projects,
                  "Inventories": Inventories,
                  "Job Templates": Job_Templates,
                  "Jobs": Jobs}

    def __init__(self, testsetup, element):
        super(HeaderMenu, self).__init__(testsetup)
        self._root_element = element

    @property
    def name(self):
        # The page is encoded in UTF-8. Convert to it.
        name = self._root_element.find_element(
                *self._name_locator).text.encode('utf-8')
        if not name:
            # If name is empty, assume Configuration menu
            name = "Home"
        return name

    def click(self):
        name = self.name
        self._root_element.find_element(*self._name_locator).click()
        current_subpage = self._item_page[name](self.testsetup).current_subpage
        if current_subpage is None:
            current_subpage = Page(self.testsetup)
        return current_subpage

    def hover(self):
        element = self._root_element.find_element(*self._name_locator)
        # Workaround for Firefox
        chain = ActionChains(self.selenium).move_to_element(element)
        if "firefox" in self.selenium.desired_capabilities["browserName"]:
            chain.move_by_offset(0, element.size['height'])
        chain.perform()

    @property
    def is_menu_submenu_visible(self):
        submenu = self._root_element.find_element(*self._menu_items_locator)
        return submenu.is_displayed()

    def sub_navigation_menu(self, value):
        # used to access on specific menu
        for menu in self.items:
            if menu.name == value:
                return menu
        raise Exception("Menu not found: '%s'. Menus: %s" % (
                value, [menu.name for menu in self.items]))
