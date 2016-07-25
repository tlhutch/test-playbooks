from selenium.webdriver.common.by import By

from common.ui.models.base import TowerPage

from common.ui.models.regions import (
    ListPagination,
    ListTable,
)


class Jobs(TowerPage):

    url_template = '/#/jobs'
    
    @property
    def list_pagination(self):
        return ListPagination(self)

    @property
    def list_table(self):
        return JobsTable(self)

    def wait_until_loaded(self):
        self.list_table.wait_for_table_to_load()


class JobsTable(ListTable):

    _root_locator = (By.CSS_SELECTOR, '#jobs_table')
