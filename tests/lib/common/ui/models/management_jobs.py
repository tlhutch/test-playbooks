'''
from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerPage
from common.ui.pages.page import Region
from common.ui.pages.regions import Clickable

from common.ui.pages.forms import SelectDropDown


class RocketLauncher(Clickable):
    _spinny = False
    _root_extension = (By.CSS_SELECTOR, "i[class$='fa fa-rocket']")

    def after_click(self):
        super(RocketLauncher, self).after_click()
        return ManagementLaunchModal(self.page)


class CalendarIcon(Clickable):
    _spinny = False
    _root_extension = (By.CSS_SELECTOR, "i[class$='fa fa-calendar']")


class ManagementCard(Region):
    _label = (By.CLASS_NAME, 'MgmtCards-label')
    _description = (By.CLASS_NAME, 'ng-binding')

    @property
    def title(self):
        return self.find_element(self._label)

    @property
    def description(self):
        return self.find_element(self._description)

    @property
    def launch(self):
        return RocketLauncher(self.page, root=self.root)

    @property
    def schedule(self):
        return CalendarIcon(self.page, root=self.root)


class ManagementLaunchModal(Region):
    _root_locator = (By.CLASS_NAME, 'ui-dialog')

    _cancel = (By.ID, 'prompt-for-days-facts-cancel')
    _close = (By.CSS_SELECTOR, 'button[class=close]')
    _granularity_keep_amount = (By.ID, 'granularity_keep_amount')
    _granularity_keep_unit = ((By.ID, 'granularity_keep_unit'), (By.XPATH, '..'))
    _keep_amount = (By.ID, 'keep_amount')
    _keep_unit = ((By.ID, 'keep_unit'), (By.XPATH, '..'))
    _launch = (By.ID, 'prompt-for-days-facts-launch')
    _title = (By.CLASS_NAME, 'ui-dialog-titlebar')

    @property
    def cancel(self):
        return Clickable(
            self.page,
            root=self.root,
            root_extension=self._cancel)

    @property
    def close(self):
        return Clickable(
            self.page,
            root=self.root,
            root_extension=self._close)

    @property
    def launch(self):
        return Clickable(
            self.page,
            root=self.root,
            root_extension=self._launch)

    @property
    def granularity_keep_amount(self):
        return Region(
            self.page,
            root=self.root,
            root_extension=self._granularity_keep_amount)

    @property
    def keep_amount(self):
        return Region(
            self.page,
            root=self.root,
            root_extension=self._keep_amount)

    @property
    def granularity_keep_unit(self):
        return SelectDropDown(
            self.page,
            root_locator=self._granularity_keep_unit)

    @property
    def keep_unit(self):
        return SelectDropDown(
            self.page,
            root_locator=self._keep_unit)

    @property
    def title(self):
        return Region(
            self.page,
            root=self.root,
            root_extension=self.title)


class ManagementJobs(TowerPage):

    _path = '/#/management_jobs'
    _cards = (By.CLASS_NAME, 'MgmtCards-card')

    @property
    def cards(self):
        elements = self.find_elements(self._cards)
        return [ManagementCard(self, root=e) for e in elements]
'''
