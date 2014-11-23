from selenium.webdriver.common.by import By
from common.ui.pages import BaseRegion, Base
from common.ui.pages.regions.lists import SortTable_Region
from common.ui.pages.regions.search import Search_Region
from common.ui.pages.regions.pagination import Pagination_Region


class Portal_Page(Base):
    '''Describes portal page'''
    _tab_title = "Portal"
    _related = {}

    _locators = {
        'job_templates_container': (By.CSS_SELECTOR, '#portal-container-job-templates'),
        'jobs_container': (By.CSS_SELECTOR, '#portal-container-jobs'),
    }

    @property
    def job_templates(self):
        return Portal_Job_Templates_Region(self.testsetup)

    @property
    def jobs(self):
        return Portal_Jobs_Region(self.testsetup)


class Portal_Job_Templates_Region(BaseRegion):
    '''
    Class that describes the 'Job Templates' region on the Portal page.
    '''
    _root_locator = (By.CSS_SELECTOR, '#portal-container-job-templates')
    _locators = {
        'search': (By.CSS_SELECTOR, '#search-widget-container'),
        'table': (By.CSS_SELECTOR, '#job_templates_table'),
        'pagination': (By.CSS_SELECTOR, '#job_template-pagination'),
    }

    @property
    def header(self):
        return self._root_element.get_attribute('text')

    @property
    def table(self):
        _related = {
            'submit-action': Portal_Page,
        }
        return SortTable_Region(self.testsetup, _root_element=self.find_element(*self._locators['table']), _related=_related)

    @property
    def pagination(self):
        return Pagination_Region(self.testsetup, _root_element=self.find_element(*self._locators['pagination']), _item_class=Portal_Page)

    @property
    def search(self):
        return Search_Region(self.testsetup, _root_element=self.find_element(*self._locators['search']), _item_class=Portal_Page)


class Portal_Jobs_Region(Portal_Job_Templates_Region):
    '''
    Class that describes the 'Jobs' region on the Portal page.
    '''
    _root_locator = (By.CSS_SELECTOR, '#portal-container-jobs')
    _locators = {
        'search': (By.CSS_SELECTOR, '#active-jobs-search-container'),
        'table': (By.CSS_SELECTOR, '#portal_jobs_table'),
        'pagination': (By.CSS_SELECTOR, '#portal_job-pagination'),
    }
