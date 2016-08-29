from selenium.webdriver.common.by import By

from qe.ui.page import Region

from qe.ui.models.base import TowerPage
from qe.ui.models.forms import SelectDropdown

__all__ = ['ManagementJobs']


class ManagementJobs(TowerPage):

    url_template = '/#/management_jobs'
    _cards = (By.CLASS_NAME, 'MgmtCards-card')

    @property
    def cards(self):
        elements = self.find_elements(*self._cards)
        return [ManagementCard(self, root=e) for e in elements]


class ManagementCard(Region):

    _label = (By.CLASS_NAME, 'MgmtCards-label')
    _description = (By.CLASS_NAME, 'ng-binding')
    _launch = (By.CSS_SELECTOR, '[aw-tool-tip*="Launch"]')
    _schedule = (By.CSS_SELECTOR, '[aw-tool-tip*="Schedule"]')

    @property
    def title(self):
        return self.find_element(*self._label)

    @property
    def description(self):
        return self.find_element(*self._description)

    @property
    def launch(self):
        return self.find_element(*self._launch)

    @property
    def schedule(self):
        return self.find_element(*self._launch)

    def is_displayed(self):
        return self.root.is_displayed()

    def open_launch_modal(self):
        self.launch.click()
        return ManagementLaunchModal(self.page)


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
        return self.find_element(*self._cancel)

    @property
    def close(self):
        return self.find_element(*self._close)

    @property
    def launch(self):
        return self.find_element(*self._launch)

    @property
    def granularity_keep_amount(self):
        return self.find_element(*self._granularity_keep_amount)

    @property
    def keep_amount(self):
        return self.find_element(*self._keep_amount)

    @property
    def granularity_keep_unit(self):
        element = self.find_element(*self._granularity_keep_unit)
        return SelectDropdown(self.page, root=element)

    @property
    def keep_unit(self):
        element = self.find_element(*self._keep_unit)
        return SelectDropdown(self.page, root=element)

    @property
    def title(self):
        return self.find_element(*self._title)
