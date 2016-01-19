from selenium.webdriver.common.by import By

from common.ui.pages.page import Region


class Spinny(Region):

    _root_locator = (By.CSS_SELECTOR, "div.spinny")
