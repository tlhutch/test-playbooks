import pytest
from tests.ui import Base_UI_Test


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Dashboard(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_active_tab(self, ui_dashboard_pg):
        '''Verify basic page layout'''
        assert ui_dashboard_pg.is_the_active_tab
        assert ui_dashboard_pg.activity_stream_btn, "Unable to locate activity stream button"
        assert ui_dashboard_pg.has_job_status_graph, "Unable to locate job status graph"
        assert ui_dashboard_pg.has_host_status_graph, "Unable to locate host status graph"
        assert ui_dashboard_pg.has_jobs_list, "Unable to locate host jobs list"
        assert ui_dashboard_pg.has_host_count_graph, "The host-count-graph is not visible to a superuser"

    def test_host_count_graph_visibility(self, ui_dashboard_pg, anonymous_user, admin_user, user_password):
        '''Verify that the host-count-graph is *not* visible for normal users'''

        assert ui_dashboard_pg.is_the_active_tab
        # Assert the host_count_graph is visible for the superuser
        assert ui_dashboard_pg.account_menu.current_user == admin_user.username
        assert ui_dashboard_pg.has_host_count_graph, "The host-count-graph is not visible to a superuser"

        # Login as a non-superuser
        with self.current_user(anonymous_user.username, user_password):
            assert ui_dashboard_pg.account_menu.current_user == anonymous_user.username
            assert ui_dashboard_pg.is_the_active_tab
            assert not ui_dashboard_pg.has_host_count_graph, "The host-count-graph is visible to a non-superuser"

        # Assert the host_count_graph is visible for the superuser
        assert ui_dashboard_pg.account_menu.current_user == admin_user.username
        assert ui_dashboard_pg.has_host_count_graph, "The host-count-graph is not visible to a superuser"

    def test_account_menu_superuser(self, ui_dashboard_pg, anonymous_user, admin_user, user_password):
        '''Verify the main_menu contents for a superuser'''

        assert ui_dashboard_pg.is_the_active_tab

        ui_dashboard_pg.account_menu.show()
        actual_items = ui_dashboard_pg.account_menu.keys()
        expected_items = [u' About Tower', u'Account Settings', u'View License', u'Contact Support', u'Monitor Tower', u'Logout']
        assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)

    def test_account_menu_non_superuser(self, ui_dashboard_pg, anonymous_user, admin_user, user_password):
        '''Verify the main_menu contents for a non-superuser'''

        with self.current_user(anonymous_user.username, user_password):
            assert ui_dashboard_pg.account_menu.current_user == anonymous_user.username
            assert ui_dashboard_pg.is_the_active_tab

            ui_dashboard_pg.account_menu.show()
            actual_items = ui_dashboard_pg.account_menu.keys()
            expected_items = [u' About Tower', u'Account Settings', u'View License', u'Contact Support', u'Logout']
            assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)

    def test_activity_stream(self, ui_dashboard_pg):
        '''Verify that the activity stream can be open and closed'''
        assert ui_dashboard_pg.activity_stream_btn, "Unable to locate activity stream button"

        # Open activity_stream
        activity_pg = ui_dashboard_pg.activity_stream_btn.click()
        assert activity_pg.is_the_active_tab
        assert activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        activity_pg.refresh_btn.click()

        # Close activity_stream
        ui_dashboard_pg = activity_pg.close_btn.click()
        assert ui_dashboard_pg.is_the_active_tab
