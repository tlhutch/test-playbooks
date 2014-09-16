import types
from selenium.webdriver.common.by import By
from common.ui.pages import BaseRegion


class Base_Button(BaseRegion):
    _root_locator = None  # provided by caller
    _item_class = None  # provided by caller
    _on_click = None  # provided by caller

    def is_displayed(self):
        return self._root_element.is_displayed()

    def is_enabled(self):
        return self._root_element.is_enabled()

    def click(self):
        self._root_element.click()
        obj = None
        # FIXME - assert it's a class
        if self._item_class is not None:
            obj = self._item_class(self.testsetup)
        if hasattr(self, '_on_click') and isinstance(self._on_click, (types.MethodType, types.InstanceType)):
            self._on_click()
        return obj


class Spinny_Button(Base_Button):
    '''Descibes a button that has a _on_click wait_for_spinny event'''
    def __init__(self, testsetup, **kwargs):
        super(Spinny_Button, self).__init__(testsetup, **kwargs)
        self._on_click = self.wait_for_spinny


class Add_Button(Spinny_Button):
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


class Select_Button(Spinny_Button):
    '''Region describing a select button'''
    _root_locator = (By.CSS_SELECTOR, '#select_btn')


class Activity_Stream_Button(Spinny_Button):
    '''Region describing the activity stream [clock] button'''
    _root_locator = (By.CSS_SELECTOR, '#stream_btn')


class Activity_Stream_Refresh_Button(Base_Button):
    '''Region describing an activity_stream [refresh] button'''
    # The following works for post-2.0.0
    _root_locator = (By.CSS_SELECTOR, '#activity-stream-refresh-btn')


class Search_Button(Spinny_Button):
    '''Region describing a search [1] magnifying glass button'''


class Reset_Button(Spinny_Button):
    '''Region describing a search [1] reset button'''
