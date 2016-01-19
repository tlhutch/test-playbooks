import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages.page import Region


class ListRegion(Region):
    '''Describes the search type options region'''
    _item_locator = (By.CSS_SELECTOR, "a")
    _unique_attribute = 'text'
    _related = {}

    def get(self, name):
        '''
        Return item with text matching the provided name
        '''
        for el in self.items():
            if el.get_attribute(self._unique_attribute) == name:
                return el
        raise Exception("No item with %s = '%s' found" % (self._unique_attribute, name))

    def items(self):
        '''
        Return a list of items identified by _item_locator
        '''
        elements = self.find_elements(self._item_locator)
        return [e for e in  elements if e.is_displayed()]

    def count(self):
        '''
        Return total number of items
        '''
        return len(self.items())

    def keys(self):
        '''
        Return a list of dictionaries mapping the region name to the selenium
        element.  For example:
            [ {name: element}, ... ]
        '''
        return [el.get_attribute(self._unique_attribute) for el in self.items()]

    def click(self, name):
        '''
        Clicks on the desired element, and returns an instance specified in _related
        '''
        el = self.get(name)
        el.click()
        self.wait_for_spinny()
        return self.get_related(name)(self.testsetup)
