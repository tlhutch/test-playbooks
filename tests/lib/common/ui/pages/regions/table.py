from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.pages.page import Region

from clickable import Clickable
from cells import NameCell


class TableHeader(Region):
    _root_extension = (By.CLASS_NAME, 'List-tableHeaderRow')
    _header_columns = (By.CLASS_NAME, 'List-tableHeader')
    _sorted_column = (By.XPATH, './/th/descendant-or-self::*[contains(@class, "fa-sort-")]/ancestor::th')
    _sortable_columns = (By.XPATH, './/th/descendant-or-self::*[contains(@class, "fa-sort")]/ancestor::th')
    _sort_status = {'fa-sort-up': 'descending', 'fa-sort-down': 'ascending'}

    @property
    def columns(self):
        return self.find_elements(self._header_columns)

    @property
    def column_names(self):
        text_values = [self._normalize_text(e.text) for e in self.columns]
        return [t for t in text_values if t]

    @property
    def sortable_columns(self):
        return self.find_elements(self._sortable_columns)

    @property
    def sortable_column_names(self):
        return [self._normalize_text(e.text) for e in self.sortable_columns]

    @property
    def sorted_column(self):
        element = self.find_element(self._sorted_column)
        return Clickable(self.page, root=element, spiny=True)

    @property
    def sorted_column_class(self):
        element = self.sorted_column.root.find_element_by_css_selector('i')
        return element.get_attribute('class')

    @property
    def sorted_column_name(self):
        return self._normalize_text(self.sorted_column.root.text)

    @property
    def sort_order(self):
        sorted_column_class_name = self.sorted_column_class
        for partial_class_name, sort_order in self._sort_status.iteritems():
            if partial_class_name in sorted_column_class_name:
                return sort_order
        raise Exception('Unable to determine colum sort order')

    def get_column_sort_order(self):
        return (self.sorted_column_name, self.sort_order)

    def set_column_sort_order(self, column_sort_order):
        (column_name, sort_order) = column_sort_order

        sortable_element = self.lookup_element(
            self._sortable_columns, text=column_name)

        sortable_column = Clickable(
            self.page, root=sortable_element, spinny=True)

        if self.sorted_column_name != column_name:
            sortable_column.click()
            self.wait.until(lambda _: self.sorted_column_name == column_name)

        if self.sort_order != sort_order:
            sortable_column.click()
            self.wait.until(lambda _: self.sort_order == sort_order)

    def is_displayed(self):
        return self.is_present() and len(self.columns) > 0

    def is_clickable(self):
        return False


class Table(Region):

    _rows = (By.CLASS_NAME, 'List-tableRow')
    _selected_row = (By.CLASS_NAME, 'List-tableRow--selected')

    _row_spec = (('name', NameCell))

    def __getitem__(self, key):
        return self.rows[key]

    @property
    def row_spec(self):
        return self.kwargs.get('row_spec', self._row_spec)

    @property
    def column_names(self):
        return self.header.column_names

    @property
    def header(self):
        return TableHeader(self.page, root=self.root)

    @property
    def rows(self):
        self.wait_until_displayed()
        return map(self._create_row, self.find_elements(self._rows))

    @property
    def selected_row(self):
        return self._create_row(self.find_element(self._selected_row))

    @property
    def sortable_column_names(self):
        return self.header.sortable_column_names

    def _create_row(self, element):
        row = {}
        for (key, region) in self.row_spec:
            self.wait.until(lambda _: element.is_displayed())
            row[key] = region(self.page, root=element)
        return row

    def get_column_sort_order(self):
        return self.header.get_column_sort_order()

    def set_column_sort_order(self, column_sort_order):
        return self.header.set_column_sort_order(column_sort_order)

    def row_is_selected(self, row):
        unique = self._row_spec[0][0]
        try:
            return row[unique].text == self.selected_row[unique].text
        except NoSuchElementException:
            return False

    def query(self, query_filter=None, sort_keys=None):
        rows = filter(query_filter, self.rows)
        if sort_keys is not None:
            return sorted(rows, key=lambda r: [r[k] for k in sort_keys])
        else:
            return rows


class FormGeneratorTable(Table):

    # Form generator table rows share the same class as the header row
    _rows = (By.CLASS_NAME, 'List-tableHeaderRow')

    @property
    def rows(self):
        table_rows = super(FormGeneratorTable, self).rows
        if len(table_rows) < 2:
            return []
        else:
            return table_rows[1:]
