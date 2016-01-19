from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from common.ui.pages.page import Region

from spinny import Spinny


class Field(Region):

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
