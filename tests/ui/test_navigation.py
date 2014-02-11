import time
import pytest
from unittestzero import Assert
from tests.ui import Base_UI_Test

@pytest.mark.usefixtures("maximized")
@pytest.mark.nondestructive
class Test_Navigation(Base_UI_Test):
    def test_tab_organizations(self, ui_organizations_pg):
        assert ui_organizations_pg.is_the_current_tab

        # FIXME - assert 'create' icon is visible (id=add_btn)
        # FIXME - assert 'activity_stream' icon is visible (id=stream_btn)
        # FIXME - assert 'organizations' table is visible (id=organizations_table)
        # FIXME - assert 'organizations' search box is visible (id=search-widget-container)

    def test_tab_navigation(self, home_page_logged_in):
        home_pg = home_page_logged_in

        # FIXME - assert default active tab

        # Click through tabs
        for tab_name in ['Organizations', 'Users', 'Teams', 'Credentials', 'Projects', 'Inventories', 'Job Templates', 'Jobs']:
            org_pg = home_pg.header.site_navigation_menu(tab_name).click()
            assert org_pg.is_the_current_tab
