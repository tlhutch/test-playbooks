from selenium.webdriver.common.by import By
from common.ui.pages.page import Region


class ListRegion(Region):
    '''Describes the search type options region'''
    _item_locator = (By.CSS_SELECTOR, "a")
    _unique_attribute = 'text'
    _related = {}

    def get(self, value):
        '''
        Return element with text matching the provided name
        '''
        for el in self.items():
            if el.get_attribute(self._unique_attribute) == value:
                return el
        raise Exception("No item with %s = '%s' found" % (self._unique_attribute, value))

    def items(self):
        '''
        Return a list of items identified by _item_locator
        '''
        elements = self.find_elements(self._item_locator)
        return [e for e in elements if e.is_displayed()]

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

    def click(self, value):
        '''
        Click on the element with a unique attribute matching the provided value
        '''
        el = self.get(value)
        self.wait.until(lambda _: el.is_enabled())
        el.click()
