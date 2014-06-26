import base
from regions.list import ListRegion, ListItem
from selenium.webdriver.common.by import By

class Dashboard(base.Base):
    '''FIXME'''
    _tab_title = "Home"
    _job_status_pane_selector = (By.CSS_SELECTOR, "div#container1")

    @property
    def job_status_pane(self):
        return ListRegion(
            self.testsetup,
            self.get_element(*self._job_status_pane_selector), self.Job_Status_Pane)

    class Job_Status_Pane(ListItem):
        _columns = ["Link", "Failed", "Total"]
        _rows = ["Server Name", "Version", "User Name",
                 "User Role", "Browser", "Browser Version",
                 "Browser OS"]

        @property
        def link(self):
            return self._item_data[0].text

        @property
        def failed(self):
            return self._item_data[1].text

        @property
        def total(self):
            return self._item_data[2].text
