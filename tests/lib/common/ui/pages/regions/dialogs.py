from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from common.ui.pages.page import Region
from clickable import Clickable


class Dialog(Region):
    _root_locator = (By.ID, 'prompt-modal')
    _close = (By.CLASS_NAME, 'Modal-exitHolder')
    _cancel = (By.ID, 'prompt_cancel_btn')
    _action = (By.ID, 'prompt_action_btn')
    _title = (By.CLASS_NAME, 'Modal-title')

    @property
    def action(self):
        return Clickable(self.page, root_locator=self._action, spinny=True)

    @property
    def cancel(self):
        return Clickable(self.page, root_locator=self._cancel, spinny=True)

    @property
    def close(self):
        return Clickable(self.page, root_locator=self._close, spinny=True)

    @property
    def title(self):
        return self.find_element(self._title)

    def click_outside(self):
        # get the x axis pixel distance between title and close button
        dx = abs(self.title.location['x'] - self.close.location['x'])

        # get the y axis pixel distance between title and cancel button
        dy = abs(self.title.location['y'] - self.cancel.location['y'])

        offset = max(dx, dy)

        action = ActionChains(self.page.driver)
        action.move_to_element_with_offset(self.root, offset, offset)
        action.click()
        action.perform()


class DeleteDialog(Dialog):

    @property
    def delete(self):
        return self.action

    def is_displayed(self):
        return super(DeleteDialog, self).is_displayed() and "DELETE" in self.title.text


class LegacyDeleteDialog(Region):
    _root_locator = (By.CSS_SELECTOR, '.ui-dialog')
    _title = (By.CSS_SELECTOR, '.ui-dialog-titlebar')
    _close = (By.CLASS_NAME, 'close')
    _delete = (By.ID, 'group-delete-ok-button')

    @property
    def close(self):
        return Clickable(self.page, root_locator=self._close, spinny=True)

    @property
    def delete(self):
        return Clickable(self.page, root_locator=self._delete, spinny=True)

    @property
    def title(self):
        return self.find_element(self._title)

    def is_displayed(self):
        return super(LegacyDeleteDialog, self).is_displayed() and 'Delete' in self.title.text
