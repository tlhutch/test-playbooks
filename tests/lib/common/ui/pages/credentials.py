from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage

from common.ui.pages.regions.forms import Checkbox
from common.ui.pages.regions.forms import Password


class SSHPassword(Password):
    _root_locator = (By.CSS_SELECTOR, '''[class='form-group Form-formGroup'][ng-show='kind.value == "ssh"']''')

    @property
    def ask(self):
        return Checkbox(self.page, root=self.root)


class Credentials(TowerCrudPage):

    _path = '/#/credentials/{index}'

    @property
    def ssh_password(self):
        return SSHPassword(self)
