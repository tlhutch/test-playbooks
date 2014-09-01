import re
from selenium.webdriver.common.by import By
from common.ui.pages import PageRegion


class Table_Region(PageRegion):
    '''Represents a table list region'''
    _hdr_row_locator = (By.CSS_SELECTOR, "thead tr")
    _hdr_locator = (By.CSS_SELECTOR, "thead th")
    _row_locator = (By.CSS_SELECTOR, "tbody tr")
    _headers = None
    _headers_index = None

    @staticmethod
    def _convert_header(header):
        '''Converts string text into something usable as an identifier.'''
        return re.sub('[^0-9a-zA-Z_]+', '', header.replace(' ', '_')).lower()

    @property
    def headers_index(self):
        if self._headers_index is None:
            self._headers_index = dict((self._convert_header(el.text), i) for i, el in enumerate(self.headers))
        return self._headers_index

    @property
    def headers(self):
        # return [el for el in self.find_elements(*self._hdr_locator)]
        if self._headers is None:
            self._headers = [el for el in self.find_elements(*self._hdr_locator)]
        return self._headers

    @property
    def rows(self):
        # return [el for el in self.find_elements(*self._row_locator)]
        for el in self.find_elements(*self._row_locator):
            yield Table_Region.Row(self.testsetup, _root_element=el, _table=self)

    class Row(PageRegion):
        '''An object representing a row in a table.'''

        _column_locator = (By.CSS_SELECTOR, "td")
        _table = None

        @property
        def columns(self):
            return self.find_elements(*self._column_locator)

        def __getattr__(self, name):
            '''Returns Row element by header name'''
            return self.columns[self._table.headers_index[name]]

        def __getitem__(self, index):
            '''Returns Row element by header index or name'''
            try:
                return self.columns[index]
            except TypeError:
                # Index isn't an int, assume it's a string
                return getattr(self, self._table._convert_header(index))


class ListRegion(PageRegion):
    '''Represents a table list region'''
    _items_locator = (By.CSS_SELECTOR, "tr")

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
