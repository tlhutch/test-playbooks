import pytest

from tests.ui import BaseTestUI

pytestmark = pytest.mark.usefixtures('maximized_window_size', 'install_license_unlimited')


class TestLogin(BaseTestUI):

    def test_login_logout(self, ui_login, default_credentials):
        """Verify a successful login and logout with default credentials
        """
        un = default_credentials['username']
        pw = default_credentials['password']

        ui_login.username.send_keys(un)
        ui_login.password.send_keys(pw)

        ui_dashboard = ui_login.login_button.click()

        assert ui_login.is_logged_in(), (
            'Unable to verify a successful login with default credentials')

        ui_dashboard.header.logout_link.click()

        assert not ui_login.is_logged_in(), (
            'Unable to verify a successful logout')

    def test_login_using_enter_key(self, ui_login, default_credentials):
        """Verify a successful login and logout with default credentials
        """
        un = default_credentials['username']
        pw = default_credentials['password']

        # Check login when using the enter key
        ui_login.username.send_keys(un)
        ui_login.password.send_keys(pw)

        ui_dashboard = ui_login.login_button.send_enter_key()

        assert ui_login.is_logged_in(), (
            'Unable to verify a successful login with default credentials')

        assert ui_dashboard.header.user == un, (
            'Unable to verify a successful login with default credentials')

    @pytest.mark.parametrize('username,password', [
        ('wrosellini', 'quintus'),
        ('wrosellini', ''),
        ('', 'quintus'),
        ('', '')
    ])
    def test_login_invalid_credentials(self, ui_login, username, password):
        """Verify that after a successful login and logout, valid credentials
        are still required
        """
        ui_login.header.wait_until_not_displayed()

        ui_login.username.send_keys(username)
        ui_login.password.send_keys(password)

        ui_login.login_button.root.click()

        assert not ui_login.is_logged_in(), (
            'Expected a failed login')

        assert ui_login.displayed_alert_errors, (
            'Expected login failure alert error(s) to be displayed')
