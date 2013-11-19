import pytest
from unittestzero import Assert
from tests.ui import Base_UI_Test

@pytest.mark.usefixtures("maximized")
@pytest.mark.nondestructive
class Test_Navigation(Base_UI_Test):
    def test_tab_navigation(self, home_page_logged_in):
        home_pg = home_page_logged_in

        org_pg = home_pg.header.site_navigation_menu("Organizations").click()
        assert org_pg.is_the_current_page

        # users
        # teams
        # credentials
        # projects
        # inventories
        # job_templates
        # jobs
