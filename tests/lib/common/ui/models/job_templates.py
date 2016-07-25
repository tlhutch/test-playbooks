from selenium.webdriver.common.by import By

from common.ui.page import Region
from common.ui.models.base import TowerPage
from common.ui.models.forms import FormPanel

from common.ui.models.regions import (
    ListPagination,
    ListTable,
    Tab,
    TagSearch,
    StatusIcon,
)

__all__ = ['JobTemplates', 'JobTemplateAdd', 'JobTemplateEdit']


class JobTemplates(TowerPage):

    url_template = '/#/job_templates'

    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_table(self):
        return JobTemplatesTable(self)

    @property
    def list_search(self):
        return TagSearch(self)

    def wait_until_loaded(self):
        self.list_table.wait_for_table_to_load()


class JobTemplateAdd(JobTemplates):

    url_template = '/#/job_templates/add'

    @property
    def forms(self):
        return [self.details]

    @property
    def details(self):
        DetailsTab(self).enable()
        return JobTemplateDetails(self)


class JobTemplateEdit(JobTemplates):

    url_template = '/#/job_templates/{id}'

    @property
    def forms(self):
        return [self.details]

    @property
    def completed_jobs(self):
        CompletedTab(self).enable()
        return FormPanel(self)

    @property
    def details(self):
        DetailsTab(self).enable()
        return JobTemplateDetails(self)

    @property
    def notifications(self):
        NotificationsTab(self).enable()
        return FormPanel(self)

    @property
    def permissions(self):
        PermissionsTab(self).enable()
        return FormPanel(self)

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.details.name.get_value())


class CompletedTab(Tab):
    _root_locator = (By.ID, 'completed_jobs_tab')

class DetailsTab(Tab):
    _root_locator = (By.ID, 'job_templates_tab')

class NotificationsTab(Tab):
    _root_locator = (By.ID, 'notifications_tab')

class PermissionsTab(Tab):
    _root_locator = (By.ID, 'permissions_tab')


class JobTemplateDetails(FormPanel):

    _region_spec = {
        'credential': {
            'region_type': 'lookup',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=credential]'),
                (By.XPATH, '..')]
        },
        'ask_machine_credential': {
            'region_type': 'checkbox',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=credential]'),
                (By.XPATH, '..')]
        },
        'inventory': {
            'required': True,
            'region_type': 'lookup',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=inventory]'),
                (By.XPATH, '..')]
        },
        'ask_inventory': {
            'region_type': 'checkbox',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=inventory]'),
                (By.XPATH, '..')]
        },
        'project': {
            'required': True,
            'region_type': 'lookup',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=project]'),
                (By.XPATH, '..')]
        },
        'cloud_credential': {
            'region_type': 'lookup',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=cloud_credential]'),
                (By.XPATH, '..')]
        },
        'name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=name]'),
                (By.XPATH, '..')]
        },
        'description': {
            'region_type': 'text_input',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=description]'),
                (By.XPATH, '..')]
        },
        'job_type': {
            'region_type': 'select',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=job_type]'),
                (By.XPATH, '..')]
        },
        'ask_job_type': {
            'region_type': 'checkbox',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=job_type]'),
                (By.XPATH, '..')]
        },
        'forks': {
            'region_type': 'form_group',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=forks]'),
                (By.XPATH, '..')]
        },
        'limit': {
            'region_type': 'text_input',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=limit]'),
                (By.XPATH, '..')]
        },
        'verbosity': {
            'region_type': 'select',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=verbosity]'),
                (By.XPATH, '..')]
        },
        'job_tags': {
            'region_type': 'text_input',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=job_tags]'),
                (By.XPATH, '..')]
        },
        'ask_job_tags': {
            'region_type': 'checkbox',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=job_tags]'),
                (By.XPATH, '..')]
        },
        'playbook': {
            'region_type': 'select',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=playbook]'),
                (By.XPATH, '..')]
        },
        'variables_parse_type': {
            'region_type': 'radio_buttons',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=variables]'),
                (By.XPATH, '..')]
        },
        'ask_variables': {
            'region_type': 'checkbox',
            'root_locator': [
                (By.CSS_SELECTOR, 'label[for=variables]'),
                (By.XPATH, '..')]
        },
        'become_enabled': {
            'region_type': 'checkbox',
            'root_locator': [
                (By.CSS_SELECTOR, '#job_templates_become_enabled_chbox'),
                (By.XPATH, '..')]
        },
        'allow_callbacks': {
            'region_type': 'checkbox',
            'root_locator': [
                (By.CSS_SELECTOR, '#job_templates_allow_callbacks_chbox'),
                (By.XPATH, '..')]
        },
    }


class JobTemplatesTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#job_templates_table')

    class Row(Region):

        _name = (By.CLASS_NAME, 'name-column')
        _description = (By.CLASS_NAME, 'description-column')
        _copy = (By.ID, 'copy-action')
        _delete = (By.ID, 'delete-action')
        _edit = (By.ID, 'edit-action')
        _launch = (By.ID, 'submit-action')
        _schedule = (By.ID, 'schedule-action')
        _status_icons = (By.CLASS_NAME, 'SmartStatus-iconContainer')

        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def description(self):
            return self.find_element(*self._description)

        @property
        def copy(self):
            return self.find_element(*self._copy)

        @property
        def delete(self):
            return self.find_element(*self._delete)

        @property
        def edit(self):
            return self.find_element(*self._edit)

        @property
        def launch(self):
            return self.find_element(*self._launch)

        @property
        def schedule(self):
            return self.find_element(*self._schedule)

        @property
        def status_icons(self):
            icons = self.find_elements(*self._status_icons)
            return [StatusIcon(self.page, root=element) for element in icons]
