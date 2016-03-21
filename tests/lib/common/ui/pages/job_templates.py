from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.page import Region
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

from common.ui.pages.regions.forms import (
    Checkbox,
    FormPanel,
    Lookup,
    RadioButtons,
    SelectDropDown,
    TextInput
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


class JobTemplatesEditDetails(FormPanel):

    _host_config = ((By.CSS_SELECTOR, '[for=host_config_key]'), (By.XPATH, '..'))
    _machine_cred = ((By.CSS_SELECTOR, '[for=credential]'), (By.XPATH, '..'))
    _inventory = ((By.CSS_SELECTOR, '[for=inventory]'), (By.XPATH, '..'))
    _project = ((By.CSS_SELECTOR, '[for=project]'), (By.XPATH, '..'))
    _cloud_cred = ((By.CSS_SELECTOR, '[for=cloud_credential]'), (By.XPATH, '..'))

    _name = (By.CSS_SELECTOR, '#job_templates_name')
    _description = (By.CSS_SELECTOR, '#job_templates_description')
    _job_type = (By.CSS_SELECTOR, '#job_templates_job_type')
    _forks = (By.CSS_SELECTOR, '#forks-number')
    _limit = (By.CSS_SELECTOR, '#job_templates_limit')
    _verbosity = (By.CSS_SELECTOR, '#job_templates_verbosity')
    _job_tags = (By.CSS_SELECTOR, '#job_templates_job_tags')
    _playbook = (By.CSS_SELECTOR, '#playbook-select')

    _variables_parse_type = (By.CSS_SELECTOR, '#job_templates_variables_parse_type')
    _ask_variables = (By.CSS_SELECTOR, '#job_templates_ask_variables_on_launch_chbox')
    _become_enabled = (By.CSS_SELECTOR, '#job_templates_become_enabled_chbox')
    _allow_callbacks = (By.CSS_SELECTOR, '#job_templates_allow_callbacks_chbox')

    @property
    def host_config_key(self):
        return Lookup(
            self.page,
            root_locator=self._host_config)

    @property
    def machine_credential(self):
        return Lookup(
            self.page,
            root_locator=self._machine_cred)

    @property
    def inventory(self):
        return Lookup(
            self.page,
            root_locator=self._inventory)

    @property
    def project(self):
        return Lookup(
            self.page,
            root_locator=self._project)

    @property
    def cloud_credential(self):
        return Lookup(
            self.page,
            root_locator=self._cloud_cred)

    @property
    def name(self):
        return TextInput(
            self.page,
            root=self.root,
            root_extension=self._name)

    @property
    def description(self):
        return TextInput(
            self.page,
            root=self.root,
            root_extension=self._description)

    @property
    def job_tags(self):
        return TextInput(
            self.page,
            root=self.root,
            root_extension=self._job_tags)

    @property
    def job_type(self):
        return SelectDropDown(
            self.page,
            root_locator=self._job_type)

    @property
    def forks(self):
        return TextInput(
            self.page,
            root=self.root,
            root_extension=self._forks)

    @property
    def limit(self):
        return TextInput(
            self.page,
            root=self.root,
            root_extension=self._limit)

    @property
    def playbook(self):
        return SelectDropDown(
            self.page,
            root_locator=self._playbook)

    @property
    def verbosity(self):
        return SelectDropDown(
            self.page,
            root_locator=self._verbosity)

    @property
    def variables_parse_type(self):
        return RadioButtons(
            self.page,
            root=self.root,
            root_extension=self._variables_parse_type)

    @property
    def ask_variables(self):
        return Checkbox(
            self.page,
            root=self.root,
            root_extension=self._ask_variables)

    @property
    def become_enabled(self):
        return Checkbox(
            self.page,
            root=self.root,
            root_extension=self._become_enabled)

    @property
    def allow_callbacks(self):
        return Checkbox(
            self.page,
            root=self.root,
            root_extension=self._allow_callbacks)


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
