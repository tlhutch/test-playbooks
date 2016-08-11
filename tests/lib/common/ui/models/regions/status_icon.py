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
    def tooltip_text(self):
        # native mouse hover events aren't supported for windows + FF so we pull the
        # tooltip data directly from the element
        if self.driver.capabilities['platform'] == 'WINDOWS':
            if self.driver.capabilities['browserName'] == 'firefox':
                return self.root.find_element_by_css_selector('a').get_attribute('aw-tool-tip')
        # move mouse to neutral location to ensure no tooltip is displayed
        footer = self.page.find_element(By.CLASS_NAME, 'Footer')
        ActionChains(self.driver).move_to_element(footer).perform()
        self.wait.until_not(lambda _: self.page.is_element_displayed(*self._tooltip))
        # move to directly over the status icon
        ActionChains(self.driver).move_to_element(self.root).perform()
        # wait for tooltip to appear
        self.wait.until(lambda _: self.page.is_element_displayed(*self._tooltip))
        # grab the icon tooltip text
        return self.page.find_element(*self._tooltip).text
