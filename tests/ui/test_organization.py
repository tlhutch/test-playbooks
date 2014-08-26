import pytest
import common.utils
from tests.ui import Base_UI_Test


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Organization(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_active_tab(self, ui_organizations_pg):
        '''Verify the basics of the organizations page'''
        assert ui_organizations_pg.is_the_active_tab

        # FIXME - assert 'organizations' table is visible (id=organizations_table)
        # FIXME - assert 'organizations' search box is visible (id=search-widget-container)

    def test_activity_stream(self, ui_organizations_pg):
        '''Verify that the organization activity stream can be open and closed'''
        assert ui_organizations_pg.has_activity_stream_button, "Unable to locate activity stream button"

        # Open activity_stream
        orgs_activity_pg = ui_organizations_pg.click_activity_stream()
        assert orgs_activity_pg.is_the_active_tab
        assert orgs_activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        orgs_activity_pg.click_refresh()

        # Close activity_stream
        ui_organizations_pg = orgs_activity_pg.click_close()
        assert ui_organizations_pg.is_the_active_tab

    def test_add(self, ui_organizations_pg):
        '''Verify basic organiation form fields'''
        assert ui_organizations_pg.has_add_button, "Unable to locate add button"

        # Click Add button
        add_pg = ui_organizations_pg.click_add()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb

        # Input Fields
        add_pg.name = "Random Organization - %s" % common.utils.random_unicode()
        add_pg.description = "Random description - %s" % common.utils.random_unicode()

        # Click Reset
        add_pg.click_reset()
        assert add_pg.name == "", "Reset button did not reset the field: name"
        assert add_pg.description == "", "Reset button did not reset the field: description"
