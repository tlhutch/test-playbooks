from selenium.webdriver.common.by import By
from common.ui.pages.page import Region


class BaseDialog(Region):
    '''
    Describes a basic modal dialog.  Should not be used directly.
    '''

    _root_locator = (By.CSS_SELECTOR, '#prompt-modal')
    _title_locator = (By.CSS_SELECTOR, 'div.modal-header')
    _body_locator = (By.CSS_SELECTOR, '#prompt-body')
    _action_btn_locator = (By.CSS_SELECTOR, '#prompt_action_button')
    _cancel_btn_locator = (By.CSS_SELECTOR, '#prompt_cancel_button')
    _close_btn_locator = (By.CSS_SELECTOR, 'button.close')

    def is_displayed(self):
        return self._root_element.is_displayed()

    @property
    def title(self):
        return self.find_element(self._title_locator).text

    @property
    def body(self):
        return self.find_element(self._body_locator).text

    @property
    def action_btn(self):
        return self.find_element(self._action_btn_locator)

    @property
    def cancel_btn(self):
        return self.find_element(self._cancel_btn_locator)

    @property
    def close_btn(self):
        return self.find_element(self._close_btn_locator)


class AlertDialog(BaseDialog):
    '''
    Describes the alert modal dialog typically used for presenting errors
    '''

    _root_locator = (By.CSS_SELECTOR, '#alert-modal')
    _title_locator = (By.CSS_SELECTOR, '#alertHeader')
    _body_locator = (By.CSS_SELECTOR, '#alert-modal-msg')
    _action_btn_locator = (By.CSS_SELECTOR, '#alert_ok_btn')

    @property
    def ok_btn(self):
        return self.find_element(self._action_btn_locator)


class PromptDialog(BaseDialog):
    '''
    Describes the prompt modal dialog typically used for presenting prompts/confirmations
    '''

    _root_locator = (By.CSS_SELECTOR, '#prompt-modal')
    _title_locator = (By.CSS_SELECTOR, 'div.modal-header')
    _body_locator = (By.CSS_SELECTOR, '#prompt-body')

    _action_btn_locator = (By.CSS_SELECTOR, '#prompt_action_button')
    _cancel_btn_locator = (By.CSS_SELECTOR, '#prompt_cancel_button')
    _close_btn_locator = (By.CSS_SELECTOR, 'button.close')
