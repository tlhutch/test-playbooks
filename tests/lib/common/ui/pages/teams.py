from selenium.webdriver.common.by import By

from common.ui.pages.base import TowerCrudPage
from common.ui.pages.regions import Table

from common.ui.pages.regions.cells import (
    NameCell,
    DescriptionCell,
    OrganizationCell,
    EditActionCell,
    DeleteActionCell
)


class TeamsTable(Table):
    _root_locator = (By.CSS_SELECTOR, '#teams_table')

    _row_spec = (
        ('name', NameCell),
        ('description', DescriptionCell),
        ('organization', OrganizationCell),
        ('edit', EditActionCell),
        ('delete', DeleteActionCell)
    )


class Teams(TowerCrudPage):

    _path = '/#/teams/{index}'

    @property
    def table(self):
        return TeamsTable(self)
