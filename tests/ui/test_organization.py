import pytest
import common.utils
from tests.ui import Base_UI_Test

@pytest.mark.usefixtures("maximized")
@pytest.mark.nondestructive
class Test_Organization(Base_UI_Test):
    def test_current_tab(self, ui_organizations_pg):
        assert ui_organizations_pg.is_the_current_tab

        assert ui_organizations_pg.has_add_button, "Unable to locate add button"
        assert ui_organizations_pg.has_activity_stream_button, "Unable to locate activity stream button"

        # FIXME - assert 'create' icon is visible (id=add_btn)
        # FIXME - assert 'activity_stream' icon is visible (id=stream_btn)
        # FIXME - assert 'organizations' table is visible (id=organizations_table)
        # FIXME - assert 'organizations' search box is visible (id=search-widget-container)

    def test_add(self, ui_organizations_pg):
        add_pg = ui_organizations_pg.click_add()

        add_pg.name = "Random Organization - %s" % common.utils.random_unicode()
        add_pg.description = "Random description - %s" % common.utils.random_unicode()
        org_pg = add_pg.click_reset()
        assert org_pg.is_the_current_tab

    def test_activity_stream(self, ui_organizations_pg):
        '''Verify that the organization activity stream can be open and closed'''
        stream_pg = ui_organizations_pg.click_activity_stream()
