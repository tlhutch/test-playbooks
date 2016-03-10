from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.regions.table import Table

from common.ui.pages.regions.forms import (
    FormPanel,
    FormSearch,
    TextInput,
    SelectDropDown,
    RadioButtons
)

from common.ui.pages.regions.cells import (
    NameCell,
    DeleteActionCell,
    EditActionCell,
    NextRunCell,
    FirstRunCell,
    FinalRunCell
)


class ScheduleTable(Table):

    _root_locator = (By.CSS_SELECTOR, '#schedules_table')

    _row_spec = (
        ('name', NameCell),
        ('first_run', FirstRunCell),
        ('next_run', NextRunCell),
        ('final_run', FinalRunCell),
        ('edit', EditActionCell),
        ('delete', DeleteActionCell)
    )


class ScheduleFormPanel(FormPanel):

    _name = (By.ID, 'schedulerName')
    _start_date = (By.ID, 'schedulerStartDt')
    _time_zone = (By.ID, 'schedulerTimeZone')
    _frequency = (By.ID, 'schedulerFrequency')
    _date_format = (By.ID, 'date-choice')

    @property
    def search(self):
        return FormSearch(self.page, root=self.root)

    @property
    def frequency(self):
        return SelectDropDown(
            self.page,
            root=self.root,
            root_extension=self._frequency)

    @property
    def date_format(self):
        return RadioButtons(
            self.page,
            root=self.root,
            root_extension=self._date_format)

    @property
    def name(self):
        return TextInput(
            self.page,
            root=self.root,
            root_extension=self._name)

    @property
    def time_zone(self):
        return SelectDropDown(
            self.page,
            root=self.root,
            root_extension=self._time_zone)

    @property
    def start_date(self):
        return TextInput(
            self.page,
            root=self.root,
            root_extension=self._start_date)


class TowerSchedulePage(TowerCrudPage):

    @property
    def form(self):
        return ScheduleFormPanel(self)

    @property
    def table(self):
        return ScheduleTable(self)


class JobTemplateSchedules(TowerSchedulePage):

    _path = '/#/job_templates/{index}/schedules'


class ManagementJobSchedules(TowerSchedulePage):

    _path = '/#/management_jobs/{index}/schedules'


class ProjectSchedules(TowerSchedulePage):

    _path = '/#/projects/{index}/schedules'
