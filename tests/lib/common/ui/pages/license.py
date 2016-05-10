from selenium.webdriver.common.by import By

from base import TowerPage
from common.ui.pages.forms import Checkbox
from common.ui.pages.page import Region
from common.ui.pages.regions import Clickable


class License(TowerPage):

    _path = '/#/license'

    _license_status = (By.XPATH, '//*[text()="License"]/following::div')

    _agree_eula = (
        (By.CSS_SELECTOR, '[class="License-details--label"]'),
        (By.CSS_SELECTOR, '[type="checkbox'))

    _license_upload = (By.ID, 'License-file')
    _submit = (By.CSS_SELECTOR, '[class="btn btn-success pull-right"]')

    _expires_on = (By.XPATH, '//*[text()="Expires On"]/following::div')
    _time_remaining = (By.XPATH, '//*[text()="Time Remaining"]/following::div')


    @property
    def license_status(self):
        return Region(self, root_locator=self._license_status)

    @property
    def agree_eula(self):
        return Checkbox(self, root_locator=self._agree_eula)

    @property
    def license_upload(self):
        return Region(self, root_locator=self._license_upload)

    @property
    def submit(self):
        return Clickable(self, root_locator=self._submit)

    @property
    def expires_on(self):
        return Region(self, root_locator=self._expires_on)

    @property
    def time_remaining(self):
        return Region(self, root_locator=self._time_remaining)

    def upload(self, file_path):
        self.license_upload.root.send_keys(file_path)
