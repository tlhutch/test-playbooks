from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerPage
from common.ui.pages.page import Region

from common.ui.pages.regions import PanelTab
from common.ui.pages.regions import Table
from common.ui.pages.regions import Search
from common.ui.pages.regions import Pagination

from common.ui.pages.regions.cells import (
    NameCell,
    IdCell,
    JobStatusCell,
    TypeCell,
    SubmitActionCell,
    DeleteActionCell,
    ScheduleActionCell,
    EditActionCell
)


class JobsTable(Table):
    _root_locator = (By.CSS_SELECTOR, '#jobs_table')

    _row_spec = (
        ('id', IdCell),
        ('name', NameCell),
        ('job_status', JobStatusCell),
        ('type', TypeCell),
        ('submit', SubmitActionCell),
        ('delete', DeleteActionCell)
    )


class JobsScheduleTable(Table):
    _root_locator = (By.CSS_SELECTOR, '#schedules_table')

    _row_spec = (
        ('name', NameCell),
        ('type', TypeCell),
        ('schedule', ScheduleActionCell),
        ('edit', EditActionCell),
        ('delete', DeleteActionCell)
    )


class JobsPanel(Region):
    _root_locator = (By.CSS_SELECTOR, '[class=Panel]')
    _search = (By.ID, 'active-jobs-search-container')

    @property
    def search(self):
        return Search(self.page, root=self.root, root_extension=self._search)

    @property
    def table(self):
        return JobsTable(self.page)


class JobsSchedulePanel(Region):
    _root_locator = (By.CSS_SELECTOR, '[class=Panel]')
    _search = (By.ID, 'search-widget-container')

    @property
    def search(self):
        return Search(self.page, root=self.root, root_extension=self._search)

    @property
    def table(self):
        return JobsScheduleTable(self.page)


class Jobs(TowerPage):

    _path = '/#/jobs'

    _jobs_tab = (By.ID, 'active_jobs_link')
    _schedules_tab = (By.ID, 'scheduled_jobs_link')
    _pagination = (By.CLASS_NAME, 'List-pagination')

    @property
    def schedules_tab(self):
        return PanelTab(self, root_locator=self._schedules_tab)

    @property
    def jobs_tab(self):
        return PanelTab(self, root_locator=self._jobs_tab)

    @property
    def pagination(self):
        return Pagination(self, root_locator=self._pagination)

    @property
    def jobs(self):
        self.jobs_tab.enable()
        return JobsPanel(self)

    @property
    def schedules(self):
        self.schedules_tab.enable()
        return JobsSchedulePanel(self)
