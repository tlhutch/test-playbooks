import time
import pytest
from unittestzero import Assert
from tests.ui import Base_UI_Test

@pytest.mark.usefixtures("maximized")
@pytest.mark.nondestructive
class Test_Dashboard(Base_UI_Test):
    def test_tab_organizations(self, ui_dashboard_pg):
        assert ui_dashboard_pg.is_the_current_tab
        print ui_dashboard_pg.job_status_pane
        for item in ui_dashboard_pg.job_status_pane.items:
            print item.link, item.failed, item.total

        # FIXME - assert 'create' icon is visible (id=add_btn)
        # FIXME - assert 'activity_stream' icon is visible (id=stream_btn)
        # FIXME - assert 'organizations' table is visible (id=organizations_table)
        # FIXME - assert 'organizations' search box is visible (id=search-widget-container)
