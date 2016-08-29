from selenium.webdriver.common.by import By

from qe.ui.page import Region
from qe.ui.models.base import TowerPage

from qe.ui.models.regions import (
    ListPagination,
    ListTable,
    Tab,
    TagSearch,
)


__all__ = ['Jobs']


class Jobs(TowerPage):

    url_template = '/#/jobs'

    @property
    def jobs(self):
        JobsTab(self).enable()
        return JobsPanel(self)

    @property
    def schedules(self):
        SchedulesTab(self).enable()
        return SchedulesPanel(self)


class JobsTab(Tab):

    _root_locator = (By.ID, 'active_jobs_link')


class JobsPanel(Region):

    @property
    def search(self):
        return TagSearch(self.page)

    @property
    def table(self):
        return JobsTable(self.page)

    @property
    def pagination(self):
        return ListPagination(self.page)


class JobsTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#jobs_table')

    class Row(Region):

        _name = (By.CLASS_NAME, 'name-column')
        _id = (By.CLASS_NAME, 'id-column')
        _type = (By.CLASS_NAME, 'type-column')
        _relaunch = (By.ID, 'submit-action')
        _delete = (By.ID, 'delete-action')
        _status = (By.CSS_SELECTOR, "i[class*='icon-job-']")

        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def id(self):
            return self.find_element(*self._id)

        @property
        def type(self):
            return self.find_element(*self._type)

        @property
        def relaunch(self):
            return self.find_element(*self._relaunch)

        @property
        def delete(self):
            return self.find_element(*self._delete)

        @property
        def status(self):
            return self.find_element(*self._status)


class SchedulesTab(Tab):

    _root_locator = (By.ID, 'scheduled_jobs_link')


class SchedulesPanel(Region):

    @property
    def pagination(self):
        return ListPagination(self.page)

    @property
    def search(self):
        return TagSearch(self.page)

    @property
    def table(self):
        return SchedulesTable(self.page)


class SchedulesTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#schedules_table')

    class Row(Region):

        _name = (By.CLASS_NAME, 'name-column')
        _job_type = (By.CLASS_NAME, 'type-column')
        _schedule = (By.ID, 'schedule-action')
        _edit = (By.CSS_SELECTOR, 'i[class*=fa-pencil]')
        _delete = (By.ID, 'delete-action')

        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def job_type(self):
            return self.find_element(*self._job_type)

        @property
        def schedule(self):
            return self.find_element(*self._schedule)

        @property
        def edit(self):
            return self.find_element(*self._edit)

        @property
        def delete(self):
            return self.find_element(*self._delete)
