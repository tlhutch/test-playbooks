from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from page import Region
from base import TowerPage

from common.ui.pages.regions import (
    DashboardGraphToggle,
    DashboardGraphTab,
    DashboardGraphDropdown,
    JobsLink,
    JobTemplatesLink,
    PageReference,
    RefreshButton
)


class Dashboard(TowerPage):

    _path = '/#/home'

    _counts_buttons = (By.CLASS_NAME, 'DashboardCounts-buttonStyle')
    _graph_tabs = (By.CLASS_NAME, 'DashboardGraphs-tab')
    _graphs = (By.CLASS_NAME, 'DashboardGraphs')
    _jobs_list = (By.CSS_SELECTOR, 'jobs-list.Dashboard-list')
    _job_status_graph = (By.CLASS_NAME, 'DashboardGraphs-graph--jobStatusGraph')
    _job_templates_list = (By.CSS_SELECTOR, 'job-templates-list.Dashboard-list')
    _host_status_graph = (By.CLASS_NAME, 'DashboardGraphs-graph--hostStatusGraph')

    @property
    def job_templates_table(self):
        return DashboardJobTemplatesTable(self)

    @property
    def jobs_table(self):
        return DashboardJobsTable(self)

    @property
    def hosts(self):
        return self.find_counts('hosts')

    @property
    def failed_hosts(self):
        return self.find_counts('failed hosts')

    @property
    def projects(self):
        return self.find_counts('projects')

    @property
    def inventories(self):
        return self.find_counts('inventories')

    @property
    def inventory_sync_failures(self):
        return self.find_counts('inventory sync failures')

    @property
    def projects_sync_failures(self):
        return self.find_counts('projects sync failures')

    @property
    def host_status_graph_tab(self):
        return self.find_graph_tab('host status')

    @property
    def job_status_graph_tab(self):
        return self.find_graph_tab('job status')

    @property
    def counts_labels(self):
        return [(count.number, count.label) for count in self._counts()]

    @property
    def refresh_button(self):
        return RefreshButton(self)

    @property
    def job_templates_list(self):
        return Region(self, root_locator=self._job_templates_list)

    @property
    def jobs_list(self):
        return Region(self, root_locator=self._jobs_list)

    @property
    def graphs(self):
        return Region(self, root_locator=self._graphs)

    @property
    def host_status_graph(self):
        return Region(self, root_locator=self._host_status_graph)

    @property
    def job_status_graph(self):
        return Region(self, root_locator=self._job_status_graph)

    @property
    def job_status_toolbar(self):
        return DashboardJobStatusToolbar(self)

    def find_counts(self, text):
        text = text.lower()

        for counts_link in self._counts():
            if text == counts_link.label:
                return counts_link

        raise NoSuchElementException

    def find_graph_tab(self, text):
        element = self.find_element_by_text(self._graph_tabs, text)
        return DashboardGraphTab(self, root=element)

    def _counts(self):
        for element in self.find_elements(self._counts_buttons):
            yield DashboardCountsLink(self, root=element)


class DashboardCountsLink(PageReference):

    _counts_number = (By.CLASS_NAME, 'DashboardCounts-number')
    _counts_label = (By.CLASS_NAME, 'DashboardCounts-label')

    @property
    def number(self):
        return self.find_element(self._counts_number).text

    @property
    def label(self):
        return self.find_element(self._counts_label).text.lower()


class DashboardTable(Region):

    _row_locator = (By.CLASS_NAME, 'List-tableRow')

    @property
    def rows(self):
        return list(self._rows())

    @property
    def row_locator(self):
        return self.kwargs.get('row_locator', self._row_locator)

    def _rows(self):
        for element in self.find_elements(self.row_locator):
            yield DashboardTableRow(self.page, root=element)


class DashboardJobTemplatesTable(DashboardTable):
    _root_locator = (By.CLASS_NAME, 'Dashboard-list--jobTemplates')


class DashboardJobsTable(DashboardTable):
    _root_locator = (By.CLASS_NAME, 'Dashboard-list--jobs')


class DashboardTableRow(Region):

    _activity = (By.CLASS_NAME, 'DashboardList-activityCell')
    _edit = (By.CLASS_NAME, 'DashboardList-actionButton--edit')
    _launch = (By.CLASS_NAME, 'DashboardList-actionButton--launch')
    _time = (By.CLASS_NAME, 'DashboardList-timeCell')
    _title = (By.CLASS_NAME, 'DashboardList-nameContainer')

    @property
    def edit(self):
        return JobTemplatesLink(self.page, root=self.find_element(self._edit))

    @property
    def launch(self):
        return JobsLink(self.page, root=self.find_element(self._launch))

    @property
    def time(self):
        return Region(self.page, root=self._find_element(self._time))

    @property
    def title(self):
        return Region(self.page, root=self.find_element(self._title))

    @property
    def activity(self):
        return Region(self.page, root=self._find_element(self._activity))


class DashboardJobStatusToolbar(Region):

    _root_locator = (By.CSS_SELECTOR, '.DashboardGraphs-graphToolbar')
    _status_buttons = (By.CSS_SELECTOR, '.DashboardGraphs-statusFilter--jobStatus')
    _type_dropdown = (By.CSS_SELECTOR, '#type-dropdown')
    _period_dropdown = (By.CSS_SELECTOR, '#period-dropdown')
    _type_items = (By.CSS_SELECTOR, '.DashboardGraphs-filterDropdownItems--jobType.dropdown-menu > li > a')
    _period_items = (By.CSS_SELECTOR, '.DashboardGraphs-filterDropdownItems--period.dropdown-menu > li > a')

    @property
    def success_status_button(self):
        return self.find_status_button('successful')

    @property
    def fail_status_button(self):
        return self.find_status_button('failed')

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

    def find_status_button(self, text):
        element = self.find_element_by_text(self._status_buttons, text)
        return DashboardGraphToggle(self.page, root=element)
