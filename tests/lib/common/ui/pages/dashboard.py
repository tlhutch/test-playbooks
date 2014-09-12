from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import Base
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button


class Dashboard_Page(Base):
    '''Describe the Home dashboard page'''
    _tab_title = "Home"
    _related = {
        'activity_stream': 'Dashboard_Activity_Page',
    }
    _locators = {
        'job_status_graph': (By.CSS_SELECTOR, '#dash-job-status-graph'),
        'host_status_graph': (By.CSS_SELECTOR, '#dash-host-status-graph'),
        'jobs_list': (By.CSS_SELECTOR, '#dash-jobs-list'),
        'host_count_graph': (By.CSS_SELECTOR, '#dash-host-count-graph'),
    }

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('activity_stream'))

    @property
    def job_status_graph(self):
        return self.find_visible_element(*self._locators['job_status_graph'])

    @property
    def has_job_status_graph(self):
        try:
            return self.job_status_graph.is_displayed()
        except NoSuchElementException:
            return False

    @property
    def host_status_graph(self):
        return self.find_visible_element(*self._locators['host_status_graph'])

    @property
    def has_host_status_graph(self):
        try:
            return self.host_status_graph.is_displayed()
        except NoSuchElementException:
            return False

    @property
    def jobs_list(self):
        return self.find_visible_element(*self._locators['jobs_list'])

    @property
    def has_jobs_list(self):
        try:
            return self.jobs_list.is_displayed()
        except NoSuchElementException:
            return False

    @property
    def host_count_graph(self):
        return self.find_visible_element(*self._locators['host_count_graph'])

    @property
    def has_host_count_graph(self):
        try:
            return self.host_count_graph.is_displayed()
        except NoSuchElementException:
            return False


class Dashboard_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all organizations'''
    _tab_title = "Home"
    _related = {
        'close': 'Dashboard_Page',
    }
