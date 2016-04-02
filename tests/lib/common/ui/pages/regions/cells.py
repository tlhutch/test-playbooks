from selenium.webdriver.common.by import By

from common.ui.pages.page import Region

from dialogs import DeleteDialog

from common.ui.pages.regions.clickable import Clickable
from common.ui.pages.regions.links import UserLink


#
# Clickable cell regions
#

class DeleteActionCell(Clickable):
    _spinny = True
    _root_extension = (By.CLASS_NAME, 'List-actionButton--delete')

    def after_click(self):
        return DeleteDialog(self.page)


class EditActionCell(Clickable):
    _root_extension = (By.CSS_SELECTOR, 'i[class*=fa-pencil]')

    def after_click(self):
        super(EditActionCell, self).after_click()
        return self.page


class SCMUpdateActionCell(Clickable):
    _spinny = True
    _root_extension = (By.ID, 'scm_update-action')
    _close_alert = (By.CSS_SELECTOR, 'button[class=close][data-target="#alert-modal"]')

    @property
    def tool_tip(self):
        return self.root.get_attribute('aw-tool-tip').lower()

    @property
    def dismiss_alert(self):
        return self.kwargs.get('dismiss_alert', True)

    def after_click(self):
        if self.dismiss_alert:
            close_alert = Region(self.page, root_locator=self._close_alert)
            if close_alert.is_displayed():
                close_alert.click()
        return super(SCMUpdateActionCell, self).after_click()


class SyncStatusCell(Clickable):
    _spinny = True
    _root_extension = (By.CSS_SELECTOR, "i[class*='icon-cloud-']")


class JobStatusCell(Clickable):
    _spinny = True
    _root_extension = (By.CSS_SELECTOR, "i[class*='icon-job-']")


class CopyActionCell(Clickable):
    _spinny = True
    _root_extension = (By.ID, 'copy-action')


class ScheduleActionCell(Clickable):
    _spinny = True
    _root_extension = (By.ID, 'schedule-action')


class SubmitActionCell(Clickable):
    _spinny = True
    _root_extension = (By.ID, 'submit-action')


class GroupUpdateActionCell(Clickable):
    _spinny = True
    _root_extension = (By.ID, 'group_update-action')


class DescriptionCell(Clickable):
    _spinny = True
    _root_extension = (By.CLASS_NAME, 'description-column')


class NameCell(Clickable):
    _root_extension = (By.CLASS_NAME, 'name-column')


class IdCell(Clickable):
    _spinny = False
    _root_extension = (By.CLASS_NAME, 'id-column')


class OrganizationCell(Clickable):
    _spinny = True
    _root_extension = (By.CLASS_NAME, 'organization-column')


class UserNameCell(UserLink):
    _root_extension = (By.CLASS_NAME, 'username-column')


#
# Text cell regions
#

class SelectCell(Region):
    _root_extension = (By.CLASS_NAME, 'select-column')


class FirstNameCell(Region):
    _root_extension = (By.CLASS_NAME, 'first_name-column')


class LastNameCell(Region):
    _root_extension = (By.CLASS_NAME, 'last_name-column')


class TypeCell(Region):
    _root_extension = (By.CLASS_NAME, 'type-column')


class FirstRunCell(Region):
    _root_extension = (By.CLASS_NAME, 'dtstart-column')


class NextRunCell(Region):
    _root_extension = (By.CLASS_NAME, 'next_run-column')


class FinalRunCell(Region):
    _root_extension = (By.CLASS_NAME, 'dtend-column')


class LastUpdatedCell(Region):
    _root_extension = (By.CLASS_NAME, 'last_updated-column')
