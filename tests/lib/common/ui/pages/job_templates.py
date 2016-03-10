from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.page import Region

from common.ui.pages.regions.forms import Lookup
from common.ui.pages.regions.tabs import PanelTab
from common.ui.pages.regions.table import Table


from common.ui.pages.regions.cells import (
    CopyActionCell,
    DeleteActionCell,
    EditActionCell,
    DescriptionCell,
    NameCell,
    ScheduleActionCell,
    SubmitActionCell
)


class JobTemplatesTable(Table):
    _root_locator = (By.CSS_SELECTOR, '#job_templates_table')

    _row_spec = (
        ('name', NameCell),
        ('delete', DeleteActionCell),
        ('edit', EditActionCell),
        ('description', DescriptionCell),
        ('schedule', ScheduleActionCell),
        ('copy', CopyActionCell),
        ('submit', SubmitActionCell)
    )


class JobTemplatesEditDetails(Region):

    _host_config = ((By.CSS_SELECTOR, '[for=host_config_key]'), (By.XPATH, '..'))
    _machine_cred = ((By.CSS_SELECTOR, '[for=credential]'), (By.XPATH, '..'))

    @property
    def host_config_key(self):
        return Lookup(self.page, root_locator=self._host_config)

    @property
    def machine_credential(self):
        return Lookup(self.page, root_locator=self._machine_cred)


class JobTemplates(TowerCrudPage):

    _path = '/#/job_templates/{index}'

    _completed_tab = (By.ID, 'organizations_tab')
    _details_tab = (By.ID, 'job_templates_tab')
    _schedules_tab = (By.ID, 'schedules_tab')

    @property
    def table(self):
        return JobTemplatesTable(self)

    @property
    def completed_jobs(self):
        self.completed_tab.enable()
        return Region(self)

    @property
    def details(self):
        self.details_tab.enable()
        return JobTemplatesEditDetails(self)

    @property
    def schedules(self):
        self.schedules_tab.enable()
        return Region(self)

    @property
    def completed_tab(self):
        return PanelTab(self, root_locator=self.completed_tab)

    @property
    def details_tab(self):
        return PanelTab(self, root_locator=self._details_tab)

    @property
    def schedules_tab(self):
        return PanelTab(self, root_locator=self._schedules_tab)
