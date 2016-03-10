from selenium.webdriver.common.by import By

from clickable import Clickable


class RefreshButton(Clickable):
    _spinny = True
    _root_locator = (By.CSS_SELECTOR, '#refresh_btn')


class SelectButton(Clickable):
    _spinny = True
    _root_locator = (By.CSS_SELECTOR, '#select_btn')


class AddButton(Clickable):
    """An add [+] button
    """
    _spinny = True
    _root_locator = (By.CSS_SELECTOR, '#add_btn')


class CloseButton(Clickable):
    """A close [x] button
    """
    _spinny = False
    _root_locator = (By.CSS_SELECTOR, '#close_btn')


class HelpButton(Clickable):
    """A help [?] button
    """
    _spinny = False
    _root_locator = (By.CSS_SELECTOR, '#help_btn')


class ClockButton(Clickable):
    """Old-Style activity stream clock button
    """
    _spinny = False
    _root_locator = (By.CSS_SELECTOR, "i[class*='fa-clock-o']")
