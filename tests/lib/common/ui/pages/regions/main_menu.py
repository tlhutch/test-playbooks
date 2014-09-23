from selenium.webdriver.common.by import By
from common.ui.pages import Dashboard_Page, Organizations_Page, Users_Page, Teams_Page, Credentials_Page, Projects_Page, Inventories, Job_Templates, Jobs
from common.ui.pages.regions.lists import List_Region


class Main_Menu(List_Region):
    '''
    '''
    _root_locator = (By.CSS_SELECTOR, '#ansible-main-menu')
    _logo_locator = (By.CSS_SELECTOR, '#ansible-brand-logo')
    _active_item_locator = (By.CSS_SELECTOR, "li.active > a")
    _region_map = {"Home": Dashboard_Page,
                   "Organizations": Organizations_Page,
                   "Users": Users_Page,
                   "Teams": Teams_Page,
                   "Credentials": Credentials_Page,
                   "Projects": Projects_Page,
                   "Inventories": Inventories,
                   "Job Templates": Job_Templates,
                   "Jobs": Jobs}

    @property
    def active_item(self):
        '''
        Return the text of the active tab
        Raises NoSuchElementException if no active tab found.
        '''
        return self.find_element(*self._active_item_locator).get_attribute('text')

    @property
    def logo(self):
        return self.selenium.find_element(*self._logo_locator)

    def keys(self):
        '''
        Return a list of dictionaries mapping the region name to the selenium
        element.  For example:
            [ {name: element}, ... ]
        '''
        return [el.get_attribute('text')for el in self.find_elements(*self._item_locator)]

    def click(self, name):
        if name == "Home":
            self.logo.click()
        else:
            self.get(name).click()
        # Wait for 'Working...' spinner to appear, and go away
        self.wait_for_spinny()
        assert name in self._region_map, "No main menu region defined for '%s'" % name
        return self._region_map[name](self.testsetup)
