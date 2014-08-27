from selenium.webdriver.common.by import By
from common.ui.pages import *


class Activity_Stream_Region(BaseRegion):
    '''Base activity stream page'''
    _breadcrumb_title = 'Activity Stream'
    _parent_object = Base
    _root_locator = (By.CSS_SELECTOR, '#stream-container')
    _refresh_btn_locator = (By.CSS_SELECTOR, '#refresh_btn')
    _close_btn_locator = (By.CSS_SELECTOR, '#close_btn')

    @property
    def refresh_button(self):
        return self.find_visible_element(*self._refresh_btn_locator)

    @property
    def has_refresh_button(self):
        try:
            return self.refresh_button.is_displayed()
        except NoSuchElementException:
            return False

    def click_refresh(self):
        self.refresh_button.click()
        self.wait_for_spinny()
        return self

    def wait_for_slidein(self):
        '''wait for activity stream to appear'''
        self.wait_for_spinny()

    def wait_for_slideout(self):
        '''wait for activity stream to disappear'''
        self.wait_for_element_not_present(*self._root_locator)

    @property
    def close_button(self):
        return self.find_visible_element(*self._close_btn_locator)

    @property
    def has_close_button(self):
        try:
            return self.close_button.is_displayed()
        except NoSuchElementException:
            return False

    def click_close(self):
        self.close_button.click()
        self.wait_for_slideout()
        return self._parent_object(self.testsetup)


class Activity_Stream_Button(BaseRegion):
    '''Region describing the activity stream button'''
    _root_locator = (By.CSS_SELECTOR, '#stream_btn')
    _item_class = None  # provided by caller (must be a subclass of Activity_Stream_Region)

    def is_displayed(self):
        return self._root_element.is_displayed()

    def click(self):
        self._root_element.click()
        obj = self._item_class(self.testsetup)
        obj.wait_for_slidein()
        return obj
