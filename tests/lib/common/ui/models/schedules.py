from selenium.webdriver.common.by import By

from common.ui.page import Region

from common.ui.models.base import TowerPage
from common.ui.models.forms import FormPanel

from common.ui.models.regions import (
    ListPagination,
    ListTable,
    TagSearch,
)


__all__ = [
    'JobTemplateSchedules',
    'JobTemplateScheduleAdd',
    'JobTemplateScheduleEdit',
    'ManagementJobSchedules',
    'ManagementJobScheduleAdd',
    'ManagementJobScheduleEdit',
    'ProjectSchedules',
    'ProjectScheduleAdd',
    'ProjectScheduleEdit',
]


class Schedules(TowerPage):

    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_table(self):
        return SchedulesTable(self)

    @property
    def list_search(self):
        return TagSearch(self)

    def wait_until_loaded(self):
        self.list_table.wait_for_table_to_load()


class ScheduleAdd(Schedules):

    @property
    def details(self):
        return ScheduleDetails(self)


class ScheduleEdit(Schedules):

    @property
    def details(self):
        return ScheduleDetails(self)


class SchedulesTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#schedules_table')

    class Row(Region):

        _name = (By.CLASS_NAME, 'name-column')
        _first_run = (By.CLASS_NAME, 'dtstart-column')
        _next_run = (By.CLASS_NAME, 'next_run-column')
        _final_run = (By.CLASS_NAME, 'dtend-column')
        _edit = (By.CSS_SELECTOR, 'i[class*=fa-pencil]')
        _delete = (By.ID, 'delete-action')

        @property
        def name(self):
            return self.find_element(*self._name)

        @property
        def first_run(self):
            return self.find_element(*self._first_run)

        @property
        def next_run(self):
            return self.find_element(*self._next_run)

        @property
        def final_run(self):
            return self.find_element(*self._final_run)

        @property
        def edit(self):
            return self.find_element(*self._edit)

        @property
        def delete(self):
            return self.find_element(*self._delete)


class ScheduleDetails(FormPanel):

    _region_spec = {
        'name': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.ID, 'schedulerName'),
                (By.XPATH, '..'))
        },
        'start_date': {
            'required': True,
            'region_type': 'text_input',
            'root_locator': (
                (By.ID, 'schedulerStartDt'),
                (By.XPATH, '..'))
        },
        'time_zone': {
            'required': True,
            'region_type': 'select',
            'root_locator': (
                (By.ID, 'schedulerTimeZone'),
                (By.XPATH, '..'))
        },
        'frequency': {
            'required': True,
            'region_type': 'select',
            'root_locator': (
                (By.ID, 'schedulerFrequency'),
                (By.XPATH, '..'))
        },
        'date_format': {
            'region_type': 'radio_buttons',
            'root_locator': (
                (By.ID, 'date-choice'),
                (By.XPATH, '..'))
        },
    }


class JobTemplateSchedules(Schedules):
    url_template = '/#/job_templates/{id}/schedules'


class JobTemplateScheduleAdd(ScheduleAdd):
    url_template = '/#/job_templates/{id}/schedules/add'


class JobTemplateScheduleEdit(ScheduleEdit):
    url_template = '/#/job_templates/{id}/schedules/{schedule_id}'


class ProjectSchedules(Schedules):
    url_template = '/#/projects/{id}/schedules'


class ProjectScheduleAdd(ScheduleAdd):
    url_template = '/#/projects/{id}/schedules/add'


class ProjectScheduleEdit(ScheduleEdit):
    url_template = '/#/projects/{id}/schedules/{schedule_id}'


class ManagementJobSchedules(Schedules):
    url_template = '/#/management_jobs/{id}/schedules'


class ManagementDetails(ScheduleDetails):

    _region_spec = ScheduleDetails._region_spec.copy()

    _region_spec['days_to_keep'] = {
        'required': True,
        'region_type': 'text_input',
        'root_locator': (
            (By.ID, 'schedulerPurgeDays'),
            (By.XPATH, '..'))
    }


class ManagementJobScheduleAdd(ScheduleAdd):

    url_template = '/#/management_jobs/{id}/schedules/add'

    @property
    def details(self):
        return ManagementDetails(self)


class ManagementJobScheduleEdit(ScheduleEdit):

    url_template = '/#/management_jobs/{id}/schedules/edit/{schedule_id}'

    @property
    def details(self):
        return ManagementDetails(self)
