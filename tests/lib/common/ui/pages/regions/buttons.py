import types
from selenium.webdriver.common.by import By
from common.ui.pages import BaseRegion


class Base_Button(BaseRegion):
    _root_locator = None  # provided by caller
    _item_class = None  # provided by caller
    _on_click = None  # provided by caller

    def is_displayed(self):
        return self._root_element.is_displayed()

    def click(self):
        self._root_element.click()
        obj = None
        # FIXME - assert it's a class
        if self._item_class is not None:
            obj = self._item_class(self.testsetup)
        if hasattr(self, '_on_click') and isinstance(self._on_click, (types.MethodType, types.InstanceType)):
            self._on_click()
        return obj


class Add_Button(Base_Button):
    '''Region describing a add [+] button'''
    _root_locator = (By.CSS_SELECTOR, '#add_btn')


class Close_Button(Base_Button):
    '''Region describing a close [x] button'''
    _root_locator = (By.CSS_SELECTOR, '#close_btn')


class Refresh_Button(Base_Button):
    '''Region describing a [refresh] button'''
    _root_locator = (By.CSS_SELECTOR, '#refresh_btn')


class Help_Button(Base_Button):
    '''Region describing a help [?] button'''
    _root_locator = (By.CSS_SELECTOR, '#help_btn')


class Activity_Stream_Button(Base_Button):
    '''Region describing the activity stream [clock] button'''
    _root_locator = (By.CSS_SELECTOR, '#stream_btn')

    def __init__(self, testsetup, **kwargs):
        super(Activity_Stream_Button, self).__init__(testsetup, **kwargs)
        self._on_click = self.wait_for_spinny


class Activity_Stream_Refresh_Button(Base_Button):
    '''Region describing an activity_stream [refresh] button'''
    # The following works for post-2.0.0
    _root_locator = (By.CSS_SELECTOR, '#activity-stream-refresh-btn')


class Page_Button(Base_Button):
    '''Region describing a pagination [1] button'''
    _root_locator = None

    def __init__(self, testsetup, **kwargs):
        super(Page_Button, self).__init__(testsetup, **kwargs)
        self._on_click = self.wait_for_spinny


class Search_Button(Page_Button):
    '''Region describing a search [1] magnifying glass button'''
    _root_locator = None

    def __init__(self, testsetup, **kwargs):
        super(Search_Button, self).__init__(testsetup, **kwargs)
        self._on_click = self.wait_for_spinny


class Reset_Button(Search_Button):
    '''Region describing a search [1] reset button'''
