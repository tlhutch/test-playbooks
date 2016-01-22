from tests.ui import BaseTestUI


class TestHeaderMenu(BaseTestUI):

    def test_header_menu_item_visibility(self, ui_dashboard, window_size):
        """Verify the visibility of header menu items for a logged in user
        """
        assert ui_dashboard.header.is_displayed(), (
            'Expected dashboard header menu to visible')

        assert ui_dashboard.header.logo.is_displayed(), (
            'Expected header inventories_link link to be visible')

        assert ui_dashboard.header.projects_link.is_displayed(), (
            'Expected header inventories_link link to be visible')

        assert ui_dashboard.header.inventories_link.is_displayed(), (
            'Expected header inventories_link link to be visible')

        assert ui_dashboard.header.job_templates_link.is_displayed(), (
            'Expected header job_templates link to be visible')

        assert ui_dashboard.header.jobs_link.is_displayed(), (
            'Expected header jobs link to be visible')

        assert ui_dashboard.header.user_link.is_displayed(), (
            'Expected header user link to be visible')

        assert ui_dashboard.header.setup_link.is_displayed(), (
            'Expected header menu setup link to be visible')

        assert ui_dashboard.header.docs_link.is_displayed(), (
            'Expected header menu docs link to be visible')

        assert ui_dashboard.header.logout_link.is_displayed(), (
            'Expected header menu logout link to be visible')

    def test_header_displays_correct_username(self, default_credentials,
                                              anonymous_user, user_password, ui_dashboard):

        default_un = default_credentials['username']

        assert ui_dashboard.header.user == default_un, (
            'Unable to verify correctly displayed username on header')

        with ui_dashboard.current_user(username=anonymous_user.username, password=user_password):
            assert ui_dashboard.header.user == anonymous_user.username.lower(), (
                'Unable to verify that the header displays the correct username')
