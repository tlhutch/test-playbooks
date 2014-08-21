import pytest
from tests.ui import Base_UI_Test

@pytest.mark.usefixtures("maximized")
@pytest.mark.nondestructive
class Test_Dashboard(Base_UI_Test):
    def test_current_tab(self, ui_dashboard_pg):
        assert ui_dashboard_pg.is_the_current_tab # FIXME

        assert ui_dashboard_pg.has_activity_stream_button, "Unable to locate activity stream button"

        assert ui_dashboard_pg.has_job_status_graph
        assert ui_dashboard_pg.has_host_status_graph
        assert ui_dashboard_pg.has_jobs_list
        assert ui_dashboard_pg.has_host_count_graph
