import pytest
from tests.ui import Base_UI_Test


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Dashboard(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_active_tab(self, ui_dashboard_pg):
        '''Verify basic page layout'''
        assert ui_dashboard_pg.is_the_active_tab, "Expecting the dashboard page"

        assert ui_dashboard_pg.has_activity_stream_button, "Unable to locate activity stream button"

        assert ui_dashboard_pg.has_job_status_graph, "Unable to locate job status graph"
        assert ui_dashboard_pg.has_host_status_graph, "Unable to locate host status graph"
        assert ui_dashboard_pg.has_jobs_list, "Unable to locate host jobs list"
        assert ui_dashboard_pg.has_host_count_graph, "The host-count-graph is not visible to a superuser"

    def test_non_superuser(self, ui_dashboard_pg, anonymous_user, admin_user, user_password):
        '''Verify that the host-count-graph is *not* visible for normal users'''

        with self.current_user(anonymous_user.username, user_password):
            assert ui_dashboard_pg.account_menu.current_user == anonymous_user.username
            assert ui_dashboard_pg.is_the_active_tab, "Expecting the dashboard page"
            assert not ui_dashboard_pg.has_host_count_graph, "The host-count-graph is visible to a non-superuser"

        assert ui_dashboard_pg.account_menu.current_user == admin_user.username
        assert ui_dashboard_pg.has_host_count_graph, "The host-count-graph is not visible to a superuser"

    def test_activity_stream(self, ui_dashboard_pg):
        '''Verify that the activity stream can be open and closed'''
        assert ui_dashboard_pg.has_activity_stream_button, "Unable to locate activity stream button"

        # Open activity_stream
        activity_pg = ui_dashboard_pg.click_activity_stream()
        assert activity_pg.is_the_active_tab
        assert activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        activity_pg.click_refresh()

        # Close activity_stream
        ui_dashboard_pg = activity_pg.click_close()
        assert ui_dashboard_pg.is_the_active_tab, "Expecting the dashboard page"
