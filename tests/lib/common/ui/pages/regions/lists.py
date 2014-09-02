import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import PageRegion


class Table_Region(PageRegion):
    '''Represents a table list region'''

    # FIXME ... define 'find_*' methods
    # FIXME ... define action methods that return appropriate class
    # FIXME ... add sort capabilities: sorted_by, sort_order

    _hdr_locator = (By.CSS_SELECTOR, "thead th")
    _row_locator = (By.CSS_SELECTOR, "tbody tr")
    _header = None
    _header_index = None

    @staticmethod
    def _convert_header(header):
        '''Converts string text into something usable as an identifier.'''
        return re.sub('[^0-9a-zA-Z_]+', '', header.replace(' ', '_')).lower()

    @property
    def header_index(self):
        if self._header_index is None:
            self._header_index = dict((self._convert_header(el.text), i) for i, el in enumerate(self.header))
        return self._header_index

    @property
    def header(self):
        # return [el for el in self.find_elements(*self._hdr_locator)]
        if self._header is None:
            self._header = [el for el in self.find_elements(*self._hdr_locator)]
        return self._header

    def find_header(self, value, contains=False):
        if contains:
            matching_cell_filter = lambda cell_text, value: value in cell_text
        else:
            matching_cell_filter = lambda cell_text, value: cell_text == value

        # Sanitize the provided value
        value = self._convert_header(value)

        for cell in self.header:
            if matching_cell_filter(self._convert_header(cell.text), value):
                return cell

        return None

    @property
    def rows(self):
        # return [el for el in self.find_elements(*self._row_locator)]
        for el in self.find_elements(*self._row_locator):
            yield Table_Region.Row(self.testsetup, _root_element=el, _table=self)

    def find_row(self, header, value):
        """
        Finds a row in the Table by iterating through each visible item.
        """
        return self.find_row_by_cells({header: value})

    def find_cell(self, header, value):
        """
        Finds an item in the Table by iterating through each visible item,
        this work used to be done by the :py:meth::`click_cell` method but
        has not been abstracted out to be called separately.
        """
        matching_cell_rows = self.find_rows_by_cells({header: value})
        try:
            if isinstance(header, basestring):
                return getattr(matching_cell_rows[0], header)
            else:
                return matching_cell_rows[0][header]
        except IndexError:
            return None

    def find_rows_by_cells(self, cells, contains=False):
        """
        A fast row finder, based on cell content.
        """
        # coerce 'cells' to a dict -- accept dicts or supertuples
        cells = dict(cells)
        cell_text_loc = './/td/descendant-or-self::*[contains(text(), "%s")]/ancestor::tr[1]'
        matching_rows_list = list()
        for value in cells.values():
            # Get all td elements that contain the value text
            matching_rows_list.extend(self.find_elements(*(By.XPATH, cell_text_loc % value)))

        # Now, find the common row elements that matched all the input cells
        # (though not yet matching values to headers)
        # Why not use set intersection here? Good question!
        # https://code.google.com/p/selenium/issues/detail?id=7011
        if False:
            rows_elements = reduce(lambda l1, l2: [item for item in l1 if item in l2],
                matching_rows_list)
        else:
            rows_elements = matching_rows_list

        # Convert them to rows
        # This is slow, which is why we do it after reducing the row element pile,
        # and not when building matching_rows_list, but it makes comparing header
        # names and expected values easy
        rows = [Table_Region.Row(self.testsetup, _root_element=el, _table=self) for el in rows_elements]

        # Only include rows where the expected values are in the right columns
        matching_rows = list()
        if contains:
            matching_row_filter = lambda heading, value: value in row[heading].text
        else:
            matching_row_filter = lambda heading, value: row[heading].text == value
        for row in rows:
            if all(matching_row_filter(*cell) for cell in cells.items()):
                matching_rows.append(row)

        return matching_rows

    def find_row_by_cells(self, cells, contains=False):
        """
        Find the first row containing cells
        """
        try:
            rows = self.find_rows_by_cells(cells, contains=contains)
            return rows[0]
        except IndexError:
            return None

    class Row(PageRegion):
        '''An object representing a row in a table.'''

        _column_locator = (By.CSS_SELECTOR, "td")
        _table = None

        @property
        def columns(self):
            '''Returns a list of column elements'''
            return self.find_elements(*self._column_locator)

        def __getattr__(self, name):
            '''Returns Cell element by header name'''
            return self.columns[self._table.header_index[name]]

        def __getitem__(self, index):
            '''Returns Cell element by header index or name'''
            try:
                return self.columns[index]
            except TypeError:
                # Index isn't an int, assume it's a string
                return getattr(self, self._table._convert_header(index))


class SortTable_Region(Table_Region):
    '''This table is the same as :py:class:`Table_Region`, but with added sorting functionality.'''

    _sort_column_locator = (By.XPATH, './/th/descendant-or-self::*[contains(@class, "fa-sort-")]/ancestor::th')

    @property
    def _sort_by_cell(self):
        try:
            return self.find_element(*self._sort_column_locator)
        except NoSuchElementException:
            return None

    @property
    def sorted_by(self):
        """Return column name what is used for sorting now.
        """
        cell = self._sort_by_cell
        if cell is None:
            return None
        return self._convert_header(cell.text)

    @property
    def sort_order(self):
        """Return order.
        """
        cell = self._sort_by_cell
        if cell is None:
            return None

        sort_class = cell.find_element_by_css_selector('i').get_attribute('class')
        if 'fa-sort-up' in sort_class:
            return 'ascending'
        elif 'fa-sort-down' in sort_class:
            return 'descending'
        else:
            return None

    def sort_by(self, header, order):
        """Sorts the table by given conditions
        """
        order = order.lower().strip()
        if header != self.sorted_by:
            # Change column to order by
            self.find_header(header).click()
            assert self.sorted_by == header, "Detected malfunction in table ordering"
        if order != self.sort_order:
            # Change direction
            self.find_header(header).click()
            assert self.sort_order == order, "Detected malfunction in table ordering"


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
