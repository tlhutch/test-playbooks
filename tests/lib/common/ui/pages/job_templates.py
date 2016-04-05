from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.regions.tabs import PanelTab
from common.ui.pages.regions.table import Table
from common.ui.pages.forms import FormPanel

from common.ui.pages.regions.cells import *  # NOQA


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


class JobTemplatesEditDetails(FormPanel):

    _region_spec = {
        'machine_credential': {
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=credential]'),
                (By.XPATH, '..'))
        },
        'inventory': {
            'required': True,
            'spinny': True,
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=inventory]'),
                (By.XPATH, '..'))
        },
        'project': {
            'required': True,
            'spinny': True,
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=project]'),
                (By.XPATH, '..'))
        },
        'cloud_credential': {
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=cloud_credential]'),
                (By.XPATH, '..'))
        },
        'name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=name]'),
                (By.XPATH, '..'))
        },
        'description': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=description]'),
                (By.XPATH, '..'))
        },
        'job_type': {
            'region_type': 'select',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=job_type]'),
                (By.XPATH, '..'))
        },
        'forks': {
            'region_type': 'form_group',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=forks]'),
                (By.XPATH, '..'))
        },
        'limit': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=limit]'),
                (By.XPATH, '..'))
        },
        'verbosity': {
            'region_type': 'select',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=verbosity]'),
                (By.XPATH, '..'))
        },
        'job_tags': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=job_tags]'),
                (By.XPATH, '..'))
        },
        'playbook': {
            'region_type': 'select',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=playbook]'),
                (By.XPATH, '..'))
        },
        'variables_parse_type': {
            'region_type': 'radio_buttons',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=variables]'),
                (By.XPATH, '..'))
        },
        'ask_variables': {
            'region_type': 'checkbox',
            'root_locator': (
                (By.CSS_SELECTOR, '#job_templates_ask_variables_on_launch_chbox'),
                (By.XPATH, '..'))
        },
        'become_enabled': {
            'region_type': 'checkbox',
            'root_locator': (
                (By.CSS_SELECTOR, '#job_templates_become_enabled_chbox'),
                (By.XPATH, '..'))
        },
        'allow_callbacks': {
            'region_type': 'checkbox',
            'root_locator': (
                (By.CSS_SELECTOR, '#job_templates_allow_callbacks_chbox'),
                (By.XPATH, '..'))
        },
    }


class JobTemplates(TowerCrudPage):

    _path = '/#/job_templates/{index}'

    _completed_tab = (By.ID, 'completed_jobs_tab')
    _details_tab = (By.ID, 'job_templates_tab')
    _schedules_tab = (By.ID, 'schedules_tab')

    @property
    def forms(self):
        return [self.details]

    @property
    def table(self):
        return JobTemplatesTable(self)

    @property
    def completed_jobs(self):
        self.completed_tab.enable()
        return FormPanel(self)

    @property
    def details(self):
        self.details_tab.enable()
        return JobTemplatesEditDetails(self)

    @property
    def schedules(self):
        self.schedules_tab.enable()
        return FormPanel(self)

    @property
    def completed_tab(self):
        return PanelTab(self, root_locator=self._completed_tab)

    @property
    def details_tab(self):
        return PanelTab(self, root_locator=self._details_tab)

    @property
    def schedules_tab(self):
        return PanelTab(self, root_locator=self._schedules_tab)
