from selenium.webdriver.common.by import By
from common.ui.pages import BaseRegion
from common.ui.pages.regions.buttons import Close_Button, Activity_Stream_Refresh_Button


class Activity_Stream_Region(BaseRegion):
    '''Base activity stream page'''
    _breadcrumb_title = 'Activity Stream'
    _root_locator = (By.CSS_SELECTOR, '#stream-container')
    _item_class = None

    @property
    def refresh_btn(self):
        return Activity_Stream_Refresh_Button(self.testsetup, _click_post=self.wait_for_spinny)

    @property
    def close_btn(self):
        return Close_Button(self.testsetup, _item_class=self._item_class, _click_post=self.wait_for_slideout)

    def wait_for_slidein(self):
        '''wait for activity stream to appear'''
        self.wait_for_spinny()

    def wait_for_slideout(self):
        '''wait for activity stream to disappear'''
        self.wait_for_element_not_present(*self._root_locator)
