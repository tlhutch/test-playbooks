from contextlib import contextmanager

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.page import Region
from common.ui.models.base import TowerPage
from common.ui.models.regions import ListTable, StatusIcon


__all__ = ['Dashboard']


class Dashboard(TowerPage):

    url_template = '/#/home'

    _count_buttons = (By.CLASS_NAME, 'DashboardCounts-buttonStyle')

    @property
    def count_buttons(self):
        elements = self.find_elements(*self._count_buttons)
        return [CountButton(self, root=e) for e in elements]

    @property
    def job_status_toolbar(self):
        return JobStatusToolbar(self)

    @property
    def recent_jobs(self):
        return RecentJobsTable(self)

    @property
    def recent_job_templates(self):
        return RecentJobTemplatesTable(self)

    def find_count_button(self, text):
        for count_button in self.count_buttons:
            if count_button.label.text.lower() == text.lower():
                return count_button
        raise NoSuchElementException


class RecentJobsTable(ListTable):

    _root_locator = (By.CLASS_NAME, 'Dashboard-list--jobs')

    class Row(Region):

        _name = (By.CLASS_NAME, 'DashboardList-nameCell')
        _time = (By.CLASS_NAME, 'DashboardList-timeCell')

        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def time(self):
            return self.find_element(*self._time)


class RecentJobTemplatesTable(ListTable):

    _root_locator = (By.CLASS_NAME, 'Dashboard-list--jobTemplates')

    class Row(Region):

        _name = (By.CLASS_NAME, 'DashboardList-nameCell')
        _launch = (By.CSS_SELECTOR, 'i[class=icon-launch]')
        _edit = (By.CSS_SELECTOR, 'i[class*=fa-pencil]')
        _status_icons = (By.CLASS_NAME, 'SmartStatus-iconContainer')

        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def launch(self):
            return self.find_element(*self._launch)

        @property
        def edit(self):
            return self.find_element(*self._edit)

        @property
        def status_icons(self):
            elements = self.find_elements(*self._status_icons)
            return [StatusIcon(self.page, root=e) for e in elements]


class CountButton(Region):

    _number = (By.CLASS_NAME, 'DashboardCounts-number')
    _label = (By.CLASS_NAME, 'DashboardCounts-label')

    @property
    def count(self):
        element = self.find_element(*self._number)
        return int(element.text)

    @property
    def label(self):
        return self.find_element(*self._label)

    def click(self):
        self.root.click()


class JobStatusToolbar(Region):

    _root_locator = (By.CSS_SELECTOR, '.DashboardGraphs-graphToolbar')

    @property
    def period(self):
        return PeriodDropdown(self.page)

    @property
    def job_type(self):
        return JobTypeDropdown(self.page)

    @property
    def status(self):
        return StatusDropdown(self.page)


class GraphDropdown(Region):

    _root_locator = None
    _items = None

    @contextmanager
    def expand(self):

        elements = self.page.find_elements(*self._items)

        def expanded(_):
            return all([e.is_displayed() for e in elements])

        if not expanded(self):
            self.root.click()
            self.wait.until(expanded)
        yield
        if expanded(self):
            self.root.click()
            self.wait.until_not(expanded)

    @property
    def options(self):
        with self.expand():
            elements = self.page.find_elements(*self._items)
            return [e.text.lower() for e in elements if e.text]

    def get_value(self):
        return self.root.text.lower()

    def set_value(self, text):
        with self.expand():
            elements = self.page.find_elements(*self._items)
            for e in elements:
                if e.text and e.text.lower() == text.lower():
                    e.click()
                    return
        raise NoSuchElementException


class PeriodDropdown(GraphDropdown):
    _root_locator = (By.CSS_SELECTOR, '#period-dropdown')
    _items = (By.CSS_SELECTOR, '.DashboardGraphs-filterDropdownItems--period.dropdown-menu > li > a')


class JobTypeDropdown(GraphDropdown):
    _root_locator = (By.CSS_SELECTOR, '#type-dropdown')
    _items = (By.CSS_SELECTOR, '.DashboardGraphs-filterDropdownItems--jobType.dropdown-menu > li > a')


class StatusDropdown(GraphDropdown):
    _root_locator = (By.CSS_SELECTOR, '#status-dropdown')
    _items = (By.CSS_SELECTOR, '[aria-labelledby="status-dropdown"] > li > a')
