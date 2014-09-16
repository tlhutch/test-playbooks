import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import PageRegion
# from common.ui.pages.regions.buttons import Base_Button


class Table_Region(PageRegion):
    '''Represents a table list region'''

    _hdr_locator = (By.CSS_SELECTOR, "thead th")
    _row_locator = (By.CSS_SELECTOR, "tbody tr")
    _header = None
    _header_index = None
    # FIXME ... define action methods that return appropriate class
    _region_map = {}

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
        # Sanitize the provided value
        value = self._convert_header(value)

        if contains:
            matching_cell_filter = lambda cell_text, value: value in cell_text
        else:
            matching_cell_filter = lambda cell_text, value: cell_text == value

        for cell in self.header:
            if matching_cell_filter(self._convert_header(cell.text), value):
                return cell

        assert False, "No header found matching '%s'" % value
        return None

    @property
    def rows(self):
        # return [el for el in self.find_elements(*self._row_locator)]
        for el in self.find_visible_elements(*self._row_locator):
            yield Table_Region.Row(self.testsetup, _root_element=el, _table=self)

    def find_row(self, header, value, contains=False):
        """
        Finds a row in the Table by iterating through each visible item.
        """
        return self.find_row_by_cells({header: value}, contains)

    def find_cell(self, header, value, contains=False):
        """
        Finds an item in the Table by iterating through each visible item,
        this work used to be done by the :py:meth::`click_cell` method but
        has not been abstracted out to be called separately.
        """
        matching_cell_rows = self.find_rows_by_cells({header: value}, contains)
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
        def toXPathStringLiteral(s):
            if "'" not in s: return "'%s'" % s
            if '"' not in s: return '"%s"' % s
            return "concat('%s')" % s.replace("'", "',\"'\",'")
        # coerce 'cells' to a dict -- accept dicts or supertuples
        cells = dict(cells)
        cell_text_loc = './/td/descendant-or-self::*[contains(text(), %s)]/ancestor::tr[1]'
        matching_rows_list = list()
        for value in cells.values():
            # Get all td elements that contain the value text
            matching_rows_list.extend(self.find_elements(*(By.XPATH, cell_text_loc % toXPathStringLiteral(value))))

        # Now, find the common row elements that matched all the input cells
        # (though not yet matching values to headers)
        # Why not use set intersection here? Good question!
        # https://code.google.com/p/selenium/issues/detail?id=7011
        if False:
            rows_elements = reduce(lambda l1, l2: [item for item in l1 if item in l2], matching_rows_list)
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

    def click_row_by_cells(self, cells, click_column=None, contains=False):
        """Click the cell at ``click_column`` in the first row matched by ``cells``

        Args:
            cells: See :py:meth:`Table.find_rows_by_cells`
            click_column: See :py:meth:`Table.click_rows_by_cells`

        """
        row = self.find_row_by_cells(cells, contains=contains)
        if click_column is None:
            row.click()
        else:
            row[click_column].click()

    def click_cells(self, cell_map):
        """Submits multiple cells to be clicked on

        Args:
            cell_map: A mapping of header names and values, representing cells to click.
                As an example, ``{'name': ['wing', 'nut']}, {'age': ['12']}`` would click on
                the cells which had ``wing`` and ``nut`` in the name column and ``12`` in
                the age column. The yaml example for this would be as follows::

                    list_items:
                        name:
                            - wing
                            - nut
                        age:
                            - 12

        Raises:
            NotAllItemsClicked: If some cells were unable to be found.

        """
        failed_clicks = []
        for header, values in cell_map.items():
            if isinstance(values, basestring):
                values = [values]
            for value in values:
                res = self.click_cell(header, value)
                if not res:
                    failed_clicks.append("%s:%s" % (header, value))
        if failed_clicks:
            raise Exception("Not all items clicked. %s" % failed_clicks)

    def click_cell(self, header, value):
        """Clicks on a cell defined in the row.

        Uses the header identifier and a value to determine which cell to click on.

        Args:
            header: A string or int, describing which column to inspect.
            value: The value to be compared when trying to identify the correct cell
                to click the cell in.

        Returns: ``True`` if item was found and clicked, else ``False``.

        """
        cell = self.find_cell(header, value)
        if cell:
            cell.click()
            return True
        else:
            return False

    class Row(PageRegion):
        '''An object representing a row in a table.'''

        _column_locator = (By.CSS_SELECTOR, "td")
        _table = None

        @property
        def columns(self):
            '''Returns a list of column elements'''
            # return self.find_elements(*self._column_locator)
            cols = list()
            for el in self.find_elements(*self._column_locator):
                # FIXME - should probably use a locator?
                # FIXME - needs to pass in a _region_map so we know what class instance to return
                if 'actions' in el.get_attribute('class'):
                    cols.append(ActionList_Region(self.testsetup, _root_element=el, _region_map=self._table._region_map))
                else:
                    cols.append(el)
            return cols

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
        """
        Return the element matching the _sort_column_locator.
        """
        try:
            return self.find_element(*self._sort_column_locator)
        except NoSuchElementException:
            return None

    @property
    def sorted_by(self):
        """
        Return column name what is used for sorting now.
        """
        cell = self._sort_by_cell
        if cell is None:
            return None
        return self._convert_header(cell.text)

    @property
    def sort_order(self):
        """
        Return current sort order (ascending, descending, None).
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
        """
        Sort the table by given conditions.
        """
        order = order.lower().strip()
        if header != self.sorted_by:
            # Change column to order by
            self.find_header(header).click()
            self.wait_for_spinny()
            assert self.sorted_by == header, "Detected malfunction in table ordering (%s != %s)" % (self.sorted_by, header)
        if order != self.sort_order:
            # Change direction
            self.find_header(header).click()
            self.wait_for_spinny()
            assert self.sort_order == order, "Detected malfunction in table ordering (%s != %s)" % (self.sort_order, order)


class List_Region(PageRegion):
    '''Describes the search type options region'''
    _item_locator = (By.CSS_SELECTOR, "a")
    _unique_attribute = 'text'

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
        return self.find_visible_elements(*self._item_locator)

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


class ActionList_Region(List_Region):
    '''Describes the list of actions in a table cell'''
    _item_locator = (By.CSS_SELECTOR, "a")
    _unique_attribute = 'id'
    _region_map = {}

    def click(self, name):
        '''
        Clicks on the desired element, and returns an instance specified in _region_map
        '''
        el = self.get(name)
        el.click()
        if name in self._region_map:
            # FIXME - what else gets passed along here?
            return self._region_map[name](self.testsetup)
        else:
            return None
