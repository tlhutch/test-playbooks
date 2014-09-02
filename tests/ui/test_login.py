import pytest
import common.utils
from tests.ui import Base_UI_Test


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Login(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_login(self, home_page_logged_in):
        '''Verify a successful login'''
        assert True

    def test_login_without_user(self, ui_login_pg):
        '''Verify that after a successful login and logout, valid credentials are still required'''
        ui_login_pg.username = 'FooBar'
        ui_login_pg.click_on_login_button()

        # Verify login failed
        assert not ui_login_pg.is_logged_in, "Expecting a failed login"
        assert ui_login_pg.has_alert_dialog, "Expecting login failure dialog"
        assert ui_login_pg.alert_dialog.body == 'Please provide a username and password before attempting to login.'

    def test_login_without_passwd(self, ui_login_pg):
        '''Verify that after a successful login and logout, valid credentials are still required'''
        ui_login_pg.password = common.utils.random_unicode()
        ui_login_pg.click_on_login_button()

        # Verify login failed
        assert not ui_login_pg.is_logged_in, "Expecting a failed login"
        assert ui_login_pg.has_alert_dialog, "Expecting login failure dialog"
        assert ui_login_pg.alert_dialog.body == 'Please provide a username and password before attempting to login.'

    def test_logout(self, home_page_logged_in):
        assert home_page_logged_in.is_logged_in, "Unable to determine if logged in"
        home_page_logged_in.logout()
        assert not home_page_logged_in.is_logged_in, "Unable to determine if logged out"

    def test_login_without_user_passwd(self, home_page_logged_in):
        '''Verify that after a successful login and logout, valid credentials are still required'''
        # Assert successful login
        assert home_page_logged_in.is_logged_in, "Unable to determine if logged in"
        # Logout
        login_pg = home_page_logged_in.logout()
        assert not login_pg.is_logged_in, "Unable to determine if logged out"
        # Attempt to login without supplying a username or password
        login_pg.click_on_login_button()
        # Assert unsuccessful login
        assert not login_pg.is_logged_in, "Not expecting to be logged in"
        assert login_pg.has_alert_dialog, "Expecting login failure dialog"
        assert login_pg.alert_dialog.body == 'Please provide a username and password before attempting to login.'
        # Dismiss the alert dialog
        login_pg.alert_dialog.ok_btn.click()
        # assert not login_pg.has_alert_dialog, "Login error dialog should have been dismissed"
