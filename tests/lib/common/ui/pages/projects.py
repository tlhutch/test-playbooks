from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.page import Region

from common.ui.pages.regions import Table
from common.ui.pages.regions import PanelTab
from common.ui.pages.regions import FormGeneratorTable
from common.ui.pages.forms import SelectDropDown

from common.ui.pages.regions.cells import (
    JobStatusCell,
    NameCell,
    TypeCell,
    SCMUpdateActionCell,
    ScheduleActionCell,
    EditActionCell,
    DeleteActionCell,
    DescriptionCell,
    LastUpdatedCell,
    FirstRunCell,
    NextRunCell,
    FinalRunCell
)


class ProjectsTable(Table):

    _root_locator = (By.CSS_SELECTOR, '#projects_table')

    _row_spec = (
        ('job_status', JobStatusCell),
        ('name', NameCell),
        ('type', TypeCell),
        ('last_updated', LastUpdatedCell),
        ('scm_update', SCMUpdateActionCell),
        ('schedule', ScheduleActionCell),
        ('edit', EditActionCell),
        ('delete', DeleteActionCell)
    )


class ProjectsSchedulesTable(FormGeneratorTable):

    _root_locator = (By.CSS_SELECTOR, '#schedules_table')

    _row_spec = (
        ('name', NameCell),
        ('first_run', FirstRunCell),
        ('next_run', NextRunCell),
        ('final_run', FinalRunCell),
        ('schedule', ScheduleActionCell),
        ('edit', EditActionCell),
        ('delete', DeleteActionCell)
    )


class ProjectsOrganizationTable(FormGeneratorTable):

    _root_locator = (By.CSS_SELECTOR, '#organizations_table')

    _row_spec = (
        ('name', NameCell),
        ('description', DescriptionCell),
        ('edit', EditActionCell),
        ('delete', DeleteActionCell)
    )


class ProjectsOrganizationsPanel(Region):

    @property
    def table(self):
        return ProjectsOrganizationTable(self.page)


class ProjectsSchedulesPanel(Region):

    @property
    def table(self):
        return ProjectsSchedulesTable(self.page)


class ProjectsDetailsPanel(Region):

    _name = (By.CSS_SELECTOR, '#project_name')
    _description = (By.CSS_SELECTOR, '#project_description')
    _organization = (By.CSS_SELECTOR, '[class=form-control][name=organization_name]')
    _scm_type = ((By.CSS_SELECTOR, '[for=scm_type]'), (By.XPATH, '..'))

    @property
    def name(self):
        return Region(self.page, root_locator=self._name)

    @property
    def description(self):
        return Region(self.page, root_locator=self._description)

    @property
    def organization(self):
        return Region(self.page, root_locator=self._organization)

    @property
    def scm_type(self):
        return SelectDropDown(self.page, root_locator=self._scm_type)


class Projects(TowerCrudPage):

    _path = '/#/projects/{index}'

    _details_tab = (By.ID, 'project_tab')
    _organizations_tab = (By.ID, 'organizations_tab')
    _schedules_tab = (By.ID, 'schedules_tab')

    @property
    def table(self):
        return ProjectsTable(self)

    @property
    def details_tab(self):
        return PanelTab(self, root_locator=self._details_tab)

    @property
    def organizations_tab(self):
        return PanelTab(self, root_locator=self._organizations_tab)

    @property
    def schedules_tab(self):
        return PanelTab(self, root_locator=self._schedules_tab)

    @property
    def details(self):
        self.details_tab.enable()
        return ProjectsDetailsPanel(self)

    @property
    def organizations(self):
        self.organizations_tab.enable()
        return ProjectsOrganizationsPanel(self)

    @property
    def schedules(self):
        self.schedules_tab.enable()
        return ProjectsSchedulesPanel(self)
