from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.ui.pages.page import Region


class Field(Region):

    _error = (By.CLASS_NAME, 'error')

    @property
    def errors(self):
        try:
            return self.find_element(self._error)
        except NoSuchElementException:
            return []

    def clear(self):
        self.root.clear()

        return self

    def send_keys(self, text):
        self.before_send_keys()
        self.root.send_keys(text)
        return self.after_send_keys()

    def after_send_keys(self):
        """Optional override for subclasses
        """
        return self

    def before_send_keys(self):
        """Optional override for subclasses
        """
        pass
