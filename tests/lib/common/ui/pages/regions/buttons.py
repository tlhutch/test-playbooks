from selenium.webdriver.common.by import By

from clickable import Clickable


class Button(Clickable):
    _spinny = True


class RefreshButton(Button):
    _spinny = True
    _root_locator = (By.CSS_SELECTOR, '#refresh_btn')


class SelectButton(Button):
    _root_locator = (By.CSS_SELECTOR, '#select_btn')


class StreamButton(Button):
    _root_locator = (By.CSS_SELECTOR, '#stream_btn')


class StreamRefreshButton(Button):
    _root_locator = (By.CSS_SELECTOR, '#activity-stream-refresh-btn')


class AddButton(Button):
    """An add [+] button
    """
    _root_locator = (By.CSS_SELECTOR, '#add_btn')


class CloseButton(Button):
    """A close [x] button
    """
    _spinny = False
    _root_locator = (By.CSS_SELECTOR, '#close_btn')


class HelpButton(Button):
    """A help [?] button
    """
    _spinny = False
    _root_locator = (By.CSS_SELECTOR, '#help_btn')


class ResetButton(Clickable):
    """A search [1] reset button
    """
    _root_locator = None


class SearchButton(Clickable):
    """A search [1] magnifying glass button
    """
    _root_locator =  None
