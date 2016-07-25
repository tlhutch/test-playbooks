from selenium.webdriver.common.by import By

from common.ui.page import Region
from common.ui.models.base import TowerPage
from common.ui.models.forms import FormPanel

from common.ui.models.regions import (
    ListPagination,
    ListTable,
    Tab,
    TagSearch,
)

__all__ = ['Projects', 'ProjectAdd', 'ProjectEdit']


class Projects(TowerPage):

    url_template = '/#/projects'

    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_table(self):
        return ProjectsTable(self)

    @property
    def list_search(self):
        return TagSearch(self)

    def wait_until_loaded(self):
        self.list_table.wait_for_table_to_load()


class ProjectAdd(Projects):

    url_template = '/#/projects/add'
    
    @property
    def details(self):
        DetailsTab(self).enable()
        return ProjectDetails(self)


class ProjectEdit(Projects):

    url_template = '/#/projects/{id}'

    @property
    def details(self):
        DetailsTab(self).enable()
        return ProjectDetails(self)

    @property
    def notifications(self):
        NotificationsTab(self).enable()
        return FormPanel(self)

    @property
    def permissions(self):
        PermissionsTab(self).enable()
        return FormPanel(self)


class DetailsTab(Tab):
    _root_locator = (By.ID, 'project_tab')

class NotificationsTab(Tab):
    _root_locator = (By.ID, 'notifications_tab')

class PermissionsTab(Tab):
    _root_locator = (By.ID, 'permissions_tab')


class ProjectDetails(FormPanel):

    _region_spec = {
        'name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=name]'),
                (By.XPATH, '..'))
        },
        'organization': {
            'required': True,
            'region_type': 'lookup',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=organization]'),
                (By.XPATH, '..'))
        },
        'scm_type': {
            'required': True,
            'region_type': 'select',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=scm_type]'),
                (By.XPATH, '..'))
        },
        'scm_url': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=scm_url]'),
                (By.XPATH, '..'))
        },
        'description': {
            'region_type': 'text_input',
            'root_locator': (
                (By.CSS_SELECTOR, 'label[for=description]'),
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


class ProjectsTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#projects_table')

    class Row(Region):
        
        _name = (By.CLASS_NAME, 'name-column')
        _description = (By.CLASS_NAME, 'description-column')
        _last_updated = (By.CLASS_NAME, 'last_updated-column')
        _delete = (By.ID, 'delete-action')
        _edit = (By.ID, 'edit-action')
        _scm_update = (By.ID, 'scm_update-action')

        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def description(self):
            return self.find_element(*self._description)

        @property
        def edit(self):
            return self.find_element(*self._edit)

        @property
        def delete(self):
            return self.find_element(*self._delete)

        @property
        def last_updated(self):
            return self.find_element(*self._last_updated)

        @property
        def scm_update(self):
            return self.find_element(*self._scm_update)

