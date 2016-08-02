from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from common.ui.page import Region


class Dialog(Region):

    _root_locator = (By.ID, 'prompt-modal')
    _close = (By.CLASS_NAME, 'Modal-exitHolder')
    _cancel = (By.ID, 'prompt_cancel_btn')
    _action = (By.ID, 'prompt_action_btn')
    _title = (By.CLASS_NAME, 'Modal-title')

    @property
    def confirm(self):
        return self.find_element(*self._action)

    @property
    def cancel(self):
        return self.find_element(*self._cancel)

    @property
    def close(self):
        return self.find_element(*self.close)

    @property
    def title(self):
        return self.find_element(*self._title)

    def click_outside(self):
        # get the x axis pixel distance between title and close button
        dx = abs(self.title.location['x'] - self.close.location['x'])
        # get the y axis pixel distance between title and cancel button
        dy = abs(self.title.location['y'] - self.cancel.location['y'])
        # get an x,y offset that will be outside of the dialog region
        offset = max(dx, dy)
        # move mouse to the offset and click
        action = ActionChains(self.page.driver)
        action.move_to_element_with_offset(self.root, offset, offset)
        action.click()
        action.perform()

    def wait_until_loaded(self):
        self.wait.until(lambda _: self.page.is_element_displayed(*self.root_locator))
