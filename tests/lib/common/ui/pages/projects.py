from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage

from common.ui.pages.regions import Table
from common.ui.pages.regions import PanelTab
from common.ui.pages.regions import FormGeneratorTable
from common.ui.pages.forms import FormPanel

from common.ui.pages.regions.cells import (DeleteActionCell, DescriptionCell, EditActionCell, FinalRunCell,
                                           FirstRunCell, JobStatusCell, LastUpdatedCell, NameCell, NextRunCell,
                                           SCMUpdateActionCell, ScheduleActionCell, TypeCell)


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


class ProjectsDetails(FormPanel):

    _region_spec = {
        'description': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=description]'),
                (By.XPATH, '..'))
        },
        'name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=name]'),
                (By.XPATH, '..'))
        },
        'scm_url': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=scm_url]'),
                (By.XPATH, '..'))
        },
        'scm_branch': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=scm_branch]'),
                (By.XPATH, '..'))
        },
        'credential': {
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=credential]'),
                (By.XPATH, '..'))
        },
    }


class ProjectsOrganizations(FormPanel):

    @property
    def table(self):
        return ProjectsOrganizationTable(self.page)


class ProjectsSchedules(FormPanel):

    @property
    def table(self):
        return ProjectsSchedulesTable(self.page)


class Projects(TowerCrudPage):

    _path = '/#/projects/{index}'

    _details_tab = (By.ID, 'project_tab')
    _organizations_tab = (By.ID, 'organizations_tab')
    _schedules_tab = (By.ID, 'schedules_tab')

    @property
    def forms(self):
        return [self.details]

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
        return ProjectsDetails(self)

    @property
    def organizations(self):
        self.organizations_tab.enable()
        return ProjectsOrganizations(self)

    @property
    def schedules(self):
        self.schedules_tab.enable()
        return ProjectsSchedules(self)
