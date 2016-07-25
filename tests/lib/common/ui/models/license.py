from selenium.webdriver.common.by import By

from common.ui.models.base import TowerPage


class License(TowerPage):

    url_template = '/#/license'

    _license_status = (By.XPATH, '//*[text()="License"]/following::div')
    _alert_modal = (By.CSS_SELECTOR, '[id="alert-modal-msg"]')
    _license_upload = (By.ID, 'License-file')
    _submit = (By.CSS_SELECTOR, '[class="btn btn-success pull-right"]')
    _expires_on = (By.XPATH, '//*[text()="Expires On"]/following::div')
    _time_remaining = (By.XPATH, '//*[text()="Time Remaining"]/following::div')
    _agree_eula = (
        (By.CSS_SELECTOR, '[class="License-details--label"]'),
        (By.CSS_SELECTOR, '[type="checkbox'))

    @property
    def license_status(self):
        return self.find_element(*self._license_status)

    @property
    def agree_eula(self):
        return self.find_element(*self._agree_eula)

    @property
    def license_upload(self):
        return self.find_element(*self._license_upload)

    @property
    def submit(self):
        return self.find_element(*self._submit)

    @property
    def expires_on(self):
        return self.find_element(*self._expires_on)

    @property
    def time_remaining(self):
        return self.find_element(*self._time_remaining)

    @property
    def alert_modal(self):
        return self.find_element(*self._alert_modal)

    def upload(self, file_path):
        self.license_upload.send_keys(file_path)

    def wait_until_alert_modal_is_displayed(self):
        self.wait.until(lambda _: self.is_element_displayed(*self._alert_modal))

    def wait_until_time_remaining_is_displayed(self):
        self.wait.until(lambda _: self.is_element_displayed(*self._time_remaining))
