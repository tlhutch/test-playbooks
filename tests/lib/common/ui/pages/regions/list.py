from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from common.ui.pages import *


class ListRegion(PageRegion):
    '''Represents a table list region'''
    _items_locator = (By.CSS_SELECTOR, "tr")

    @property
    def items(self):
        '''Returns a list of items represented by _item_cls'''
        return [self._item_cls(self.testsetup, web_element)
                for web_element in self._root_element.find_elements(*self._items_locator)]


class ListItem(PageRegion):
    '''Represents an item in the list'''
    _item_data_locator = (By.CSS_SELECTOR, "td")

    def click(self):
        '''Click on the item, which will select it in the list'''
        self._item_data[0].click()
        self.wait_for_spinny()

    @property
    def _item_data(self):  # IGNORE:C0111
        return [web_element
                for web_element in self._root_element.find_elements(*self._item_data_locator)]
