from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.page import Region


__all__ = ['ListTable']


class ListTable(Region):

    class Row(Region):
        pass

    _root_locator = None
    _badge = (By.CSS_SELECTOR, '.badge')
    _noitems = (By.CLASS_NAME, 'List-noItems')
    _rows = (By.CLASS_NAME, 'List-tableRow')
    _selected_row = (By.CLASS_NAME, 'List-tableRow--selected')

    @property
    def header(self):
        return TableHeader(self.page, root=self.root)

    @property
    def rows(self):
        elements = self.find_elements(*self._rows)
        return [self.Row(self.page, root=e) for e in elements]

    @property
    def selected_row(self):
        element = self.find_element(*self._selected_row)
        return self.Row(self.page, root=element)

    def query(self, query_filter):
        return [r for r in self.rows if query_filter(r)]

    def is_table_loaded(self):
        locators = [self._badge, self._noitems]
        return any(self.page.is_element_displayed(*loc) for loc in locators)

    def wait_for_table_to_load(self):
        self.wait.until(lambda _: self.is_table_loaded())


class TableHeader(Region):

    _sortable_columns = (By.XPATH, './/th/descendant-or-self::*[contains(@class, "fa-sort")]/ancestor::th')
    _sorted_column = (By.XPATH, './/th/descendant-or-self::*[contains(@class, "fa-sort-")]/ancestor::th')

    @property
    def sortable_columns(self):
        return self.find_elements(*self._sortable_columns)

    @property
    def sorted_column(self):
        return self.find_element(*self._sorted_column)

    def _find_sortable_column(self, text):
        for sortable_column in self.sortable_columns:
            if sortable_column.text.lower() == text:
                return sortable_column
        raise ValueError('Unable to find sortable column: {0}'.format(text))

    def get_sort_status(self):
        # get sorted column and sorted column name
        sorted_column = self.sorted_column
        sorted_column_name = sorted_column.text.lower()
        # get column status element and class name
        status_element = sorted_column.find_element_by_css_selector('i')
        status_class_name = status_element.get_attribute('class')
        # determine and return sort status tuple
        if 'fa-sort-up' in status_class_name:
            return (sorted_column_name, 'descending')
        if 'fa-sort-down' in status_class_name:
            return (sorted_column_name, 'ascending')
        raise ValueError('could not determine sort status')

    def set_sort_status(self, sort_status):
        assert isinstance(sort_status, tuple) and len(sort_status) == 2
        assert sort_status[1] in ('ascending', 'descending')

        if sort_status != self.get_sort_status():
            self._find_sortable_column(sort_status[0]).click()
            if sort_status != self.get_sort_status():
                self._find_sortable_column(sort_status[0]).click()

    def get_sort_status_options(self):
        sortable_column_names = [e.text.lower() for e in self.sortable_columns]
        sorting_options = []
        for name in sortable_column_names:
            sorting_options.append((name, 'ascending'))
            sorting_options.append((name, 'descending'))
        return sorting_options

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.page.is_element_displayed(*self._sorted_column))

