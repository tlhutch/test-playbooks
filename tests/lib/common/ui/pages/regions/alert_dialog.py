from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from common.ui.pages import *

class Alert_Dialog(Page):
    '''
    Describes the alert modal dialog typically used for presenting errors
    '''

    _alert_dialog_locator = (By.CSS_SELECTOR, '#alert-modal')
    _alert_title_locator = (By.CSS_SELECTOR, '#alertHeader')
    _alert_body_locator = (By.CSS_SELECTOR, '#alert-modal-msg')
    _alert_ok_btn_locator = (By.CSS_SELECTOR, '#alert_ok_btn')
    _alert_close_btn_locator = (By.CSS_SELECTOR, '#FIXME') # FIXME - there is no DOM id

    def __init__(self, testsetup):
        super(Alert_Dialog, self).__init__(testsetup)
        self._root_element = self.selenium.find_element(*self._alert_dialog_locator)

    def is_displayed(self):
        return self._root_element.is_displayed()

    @property
    def title(self):
        return self._root_element.find_element(*self._alert_title_locator).text

    @property
    def body(self):
        return self._root_element.find_element(*self._alert_body_locator).text

    @property
    def ok_btn(self):
        return self._root_element.find_element(*self._alert_ok_btn_locator)

    def click_ok_btn(self):
        return self.ok_btn.click()

