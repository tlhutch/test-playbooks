from selenium.webdriver.common.by import By

from common.ui.pages.page import Region


class SearchDropDown(Region):

    _root_locator = None

    _toggle_button = (By.ID, 'search_field_ddown')
    _options = (By.ID, '')
