from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from common.ui.page import Region


class StatusIcon(Region):

    _tooltip = (By.CSS_SELECTOR, '[role="tooltip"]')

    def click(self):
        self.root.click()

    @property
    def href(self):
        return self.root.get_attribute('href')

    @property
    def tooltip(self):
        # hover over status icon
        ActionChains(self.driver).move_to_element(self.root).perform()
        # wait for tooltip to appear
        self.wait.until(lambda _: self.page.is_element_displayed(*self._tooltip))
        # grab the tooltip element
        return self.page.find_element(*self._tooltip)
