from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from common.ui.pages.page import Region

from spinny import Spinny


class Clickable(Region):

    _spinny = False

    def click(self, skip_spinny=False):

        self.before_click()
        self.wait_until_clickable()

        self.root.click()

        if self._spinny and not skip_spinny:
            self.wait_for_spinny()

        return self.after_click()

    def after_click(self):
        """Optional override for subclasses
        """
        return self.page

    def before_click(self):
        """Optional override for subclasses
        """
        pass

    def send_enter_key(self, skip_spinny=False):

        self.before_click()
        self.wait_until_clickable()

        self.root.send_keys(Keys.RETURN)

        if self._spinny and not skip_spinny:
            self.wait_for_spinny()

        return self.after_click()

    def wait_for_spinny(self):
        try:
            self.spinny.wait_until_displayed()
        except TimeoutException:
            pass

        self.spinny.wait_until_not_displayed()

    @property
    def spinny(self):
        return Spinny(self.page)
