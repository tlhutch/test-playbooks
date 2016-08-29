from selenium.webdriver.common.by import By

from qe.ui.page import Region
from qe.ui.models.base import TowerPage

from qe.ui.models.regions import (
    ListTable,
    ListPagination,
    TagSearch,
)

__all__ = ['ManageInventory']


class ManageInventory(TowerPage):

    url_template = '/#/inventories/{id}/manage'

    @property
    def groups(self):
        return GroupsList(self)

    @property
    def hosts(self):
        return HostsList(self)


class GroupsList(Region):

    _root_locator = (By.CSS_SELECTOR, '#groups-list')

    _add = (By.CSS_SELECTOR, '[aw-tool-tip*="Create"]')
    _run = (By.CSS_SELECTOR, '[aw-tool-tip*="Select"]')

    @property
    def add(self):
        return self.find_element(*self._add)

    @property
    def run_command(self):
        return self.find_element(*self._run)

    @property
    def table(self):
        return GroupsTable(self.page)

    @property
    def pagination(self):
        return ListPagination(self.page, root=self.root)

    @property
    def search(self):
        return TagSearch(self.page, root=self.root)


class HostsList(Region):

    _root_locator = (By.CSS_SELECTOR, '#hosts-list')

    _add = (By.CSS_SELECTOR, '[aw-tool-tip*="Create"]')
    _system_tracking = (By.CSS_SELECTOR, '[aw-tool-tip*="Select"]')

    @property
    def add(self):
        return self.find_element(*self._add)

    @property
    def system_tracking(self):
        return self.find_element(*self._system_tracking)

    @property
    def table(self):
        return HostsTable(self.page)

    @property
    def pagination(self):
        return ListPagination(self.page, root=self.root)

    @property
    def search(self):
        return TagSearch(self.page, root=self.root)


class GroupsTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#groups_table')

    class Row(Region):

        _name = (By.CLASS_NAME, 'name-column')
        _copy = (By.ID, 'copy-action')
        _delete = (By.ID, 'delete-action')
        _edit = (By.ID, 'edit-action')
        _update = (By.ID, 'group_update-action')
        _job_status = (By.CSS_SELECTOR, "i[class*='icon-job-']")
        _update_status = (By.CSS_SELECTOR, "i[class*='icon-cloud-']")

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
        def name(self):
            return self.find_element(*self._name)

        @property
        def job_status(self):
            return self.find_element(*self._job_status)

        @property
        def update(self):
            return self.find_element(*self._update)

        @property
        def update_status(self):
            return self.find_element(*self._update_status)


class HostsTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#hosts_table')

    class Row(Region):

        _name = (By.CLASS_NAME, 'name-column')
        _copy = (By.ID, 'copy-action')
        _delete = (By.ID, 'delete-action')
        _edit = (By.ID, 'edit-action')
        _job_status = (By.CSS_SELECTOR, "i[class*='icon-job-']")

        @property
        def name(self):
            return self.find_element(*self._name)

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
        def update(self):
            return self.find_element(*self._edit)

        @property
        def job_status(self):
            return self.find_element(*self._job_status)
