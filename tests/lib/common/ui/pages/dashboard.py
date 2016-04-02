from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from page import Region
from base import TowerPage

from common.ui.pages.regions import (
    Clickable,
    Link,
    PanelTab,
    PanelToggleTab,
    Table,
)

from common.ui.pages.regions.cells import *  # NOQA


class Dashboard(TowerPage):

    _path = '/#/home'

    _count_buttons = (By.CLASS_NAME, 'DashboardCounts-buttonStyle')
    _job_status_graph_tab = (By.CLASS_NAME, 'DashboardGraphs-tab--firstTab')
    _host_status_graph_tab = (By.CLASS_NAME, 'DashboardGraphs-tab--lastTab')
    _jobs_list = (By.CSS_SELECTOR, 'jobs-list.Dashboard-list')
    _job_status_graph = (By.CLASS_NAME, 'DashboardGraphs-graph--jobStatusGraph')
    _host_status_graph = (By.CLASS_NAME, 'DashboardGraphs-graph--hostStatusGraph')
    _clock_button = (By.CSS_SELECTOR, "i[class*='fa-clock-o']")

    @property
    def hosts(self):
        return self._locate_count_button('hosts')

    @property
    def failed_hosts(self):
        return self._locate_count_button('failed hosts')

    @property
    def projects(self):
        return self._locate_count_button('projects')

    @property
    def inventories(self):
        return self._locate_count_button('inventories')

    @property
    def inventory_sync_failures(self):
        return self._locate_count_button('inventory sync failures')

    @property
    def projects_sync_failures(self):
        return self._locate_count_button('projects sync failures')

    @property
    def counts(self):
        count_names = [
            'jobs',
            'hosts',
            'failed hosts',
            'projects',
            'inventories',
            'inventory sync failures',
            'projects sync failures']

        for name in count_names:
            yield self._locate_count_button(name)

    @property
    def jobs(self):
        return DashboardJobsPanel(self)

    @property
    def job_templates(self):
        return DashboardJobTemplatesPanel(self)

    @property
    def host_status_graph_tab(self):
        return PanelTab(self, root_locator=self._host_status_graph_tab)

    @property
    def job_status_graph_tab(self):
        return PanelTab(self, root_locator=self._job_status_graph_tab)

    @property
    def host_status_graph(self):
        if not self.host_status_graph_tab.is_enabled():
            self.host_status_graph_tab.click()
        return Region(self, root_locator=self._host_status_graph)

    @property
    def job_status_graph(self):
        if not self.job_status_graph_tab.is_enabled():
            self.job_status_graph_tab.click()
        return Region(self, root_locator=self._job_status_graph)

    @property
    def job_status_toolbar(self):
        if not self.job_status_graph_tab.is_enabled():
            self.job_status_graph_tab.click()
        return DashboardJobStatusToolbar(self)

    def has_clock_button(self):
        return Region(self, root_locator=self._clock_button).is_present()

    def _locate_count_button(self, text):
        text = text.lower()
        results = self.find_elements(self._counts_buttons)
        try:
            element = next(e for e in results if text in e.text.lower())
        except StopIteration:
            raise NoSuchElementException
        else:
            return CountsLink(self, root=element, spinny=True)


class CountsLink(Link):

    _root_locator = None

    _number = (By.CLASS_NAME, 'DashboardCounts-number')
    _label = (By.CLASS_NAME, 'DashboardCounts-label')

    @property
    def number(self):
        element = self.find_element(self._number)
        return element.text

    @property
    def label(self):
        element = self.find_element(self._label)
        return self._normalize_text(element.text)


class DashboardNameCell(Clickable):
    _root_extension = (By.CLASS_NAME, 'DashboardList-nameCell')


class DashboardTimeCell(Region):
    _root_extension = (By.CLASS_NAME, 'DashboardList-timeCell')


class DashboardJobsPanel(Region):

    _root_locator = (By.CLASS_NAME, 'Dashboard-list--jobs')
    _table = (By.CLASS_NAME, 'DashboardList-container')
    _no_content_message = (By.CLASS_NAME, 'Dashboard-list--noJobs')
    _view_all = (By.CLASS_NAME, 'Dashboard-list--viewAll')

    _row_spec = (
        ('name', DashboardNameCell),
        ('time', DashboardTimeCell)
    )

    @property
    def table(self):
        element = self.find_element(self._table)
        return Table(self.page, root=element, row_spec=self._row_spec)

    @property
    def view_all(self):
        element = self.find_element(self._view_all)
        return Clickable(self.page, root=element, spinny=True)

    @property
    def no_content_message(self):
        element = self.find_element(self._no_content_message)
        return Region(self.page, root=element)


class DashboardJobTemplatesPanel(Region):

    _root_locator = (By.CLASS_NAME, 'Dashboard-list--jobTemplates')
    _table = (By.CLASS_NAME, 'DashboardList-container')
    _no_content_message = (By.CLASS_NAME, 'Dashboard-list--noJobs')
    _view_all = (By.CLASS_NAME, 'Dashboard-list--viewAll')

    _row_spec = (
        ('name', DashboardNameCell),
        ('edit', EditActionCell),
        ('submit', SubmitActionCell)
    )

    @property
    def table(self):
        element = self.find_element(self._table)
        return Table(self.page, root=element, row_spec=self._row_spec)

    @property
    def view_all(self):
        element = self.find_element(self._view_all)
        return Clickable(self.page, root=element, spinny=True)

    @property
    def no_content_message(self):
        element = self.find_element(self._no_content_message)
        return Region(self.page, root=element)


class DashboardGraphDropdown(Clickable):

    _root_locator = None
    _item_locator = None

    @property
    def item_locator(self):
        return self.kwargs.get('item_locator', self._item_locator)

    def _items(self):
        for element in self.page.find_elements(self.item_locator):
            yield Clickable(self.page, root=element)

    def _collapse(self):
        item = next(self._items())

        if item.is_displayed():
            self.click()
            item.wait_until_not_displayed()

    def _expand(self):
        item = next(self._items())

        if not item.is_displayed():
            self.click()
            item.wait_until_displayed()

    @property
    def selected_option(self):
        return self.normalized_text

    @property
    def options(self):
        self._expand()
        options = [item.normalized_text for item in self._items()]
        self._collapse()
        return options

    def select(self, text):
        self._expand()

        for item in self._items():
            if item.normalized_text == text:
                item.click()
                self._collapse()
                return

        self._collapse()
        raise NoSuchElementException


class DashboardJobStatusToolbar(Region):

    _root_locator = (By.CSS_SELECTOR, '.DashboardGraphs-graphToolbar')
    _status_buttons = (By.CLASS_NAME, 'DashboardGraphs-statusFilter--jobStatus')
    _type_dropdown = (By.CSS_SELECTOR, '#type-dropdown')
    _period_dropdown = (By.CSS_SELECTOR, '#period-dropdown')
    _type_items = (By.CSS_SELECTOR, '.DashboardGraphs-filterDropdownItems--jobType.dropdown-menu > li > a')
    _period_items = (By.CSS_SELECTOR, '.DashboardGraphs-filterDropdownItems--period.dropdown-menu > li > a')

    @property
    def success_status_button(self):
        for element in self.page.find_elements(self._status_buttons):
            if 'success' in element.get_attribute('ng-class').lower():
                return PanelToggleTab(self.page, root=element)
        raise NoSuchElementException

    @property
    def fail_status_button(self):
        for element in self.page.find_elements(self._status_buttons):
            if 'failed' in element.get_attribute('ng-class').lower():
                return PanelToggleTab(self.page, root=element)
        raise NoSuchElementException

    @property
    def period_dropdown(self):
        return DashboardGraphDropdown(
            self.page,
            root_locator=self._period_dropdown,
            item_locator=self._period_items)

    @property
    def job_types_dropdown(self):
        return DashboardGraphDropdown(
            self.page,
            root_locator=self._type_dropdown,
            item_locator=self._type_items)
