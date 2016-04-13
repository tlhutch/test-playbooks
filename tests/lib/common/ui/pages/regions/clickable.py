from selenium.webdriver.common.keys import Keys

from common.ui.pages.page import Region

from spinny import Spinny


class Clickable(Region):

    _spinny = False

    @property
    def value(self):
        return self.normalized_text

    @property
    def spinny(self):
        return self.kwargs.get('spinny', self._spinny)

    def click(self):
        self.before_click()
        self.wait_until_clickable()

        self.wait.until(lambda _: self._click_success())

        if self.spinny:
            self.wait_for_spinny()

        return self.after_click()

    def _click_success(self):
        try:
            self.root.click()
            return True
        except:
            return False

    def after_click(self):
        """Optional override hook for subclasses
        """
        return self.page

    def before_click(self):
        """Optional override hook for subclasses
        """
        pass

    def send_enter_key(self):
        self.before_click()
        self.send_keys(Keys.RETURN)

        if self.spinny:
            self.wait_for_spinny()

        return self.after_click()

    def wait_for_spinny(self):
        """Wait for spinny to appear and then disappear
        """
        Spinny(self.page).wait_cycle()
