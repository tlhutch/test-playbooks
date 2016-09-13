import pytest
from selenium.common.exceptions import TimeoutException

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures('max_window')
]


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
def test_login_logout(ui_login, default_credentials):
    """Verify a successful login and logout with default credentials
    """
    username = default_credentials['username']
    password = default_credentials['password']

    try:
        ui_login.login_with_enter_key(username, password)
    except TimeoutException:
        pytest.fail('Unable to verify a successful login')
    try:
        ui_login.logout()
    except TimeoutException:
        pytest.fail('Unable to verify a successful logout')


@pytest.mark.parametrize('username,password', [
    ('wrosellini', 'quintus'),
    ('wrosellini', ''),
    ('', 'quintus'),
    ('', '')
])
def test_login_invalid_credentials(ui_login, username, password):
    """Verify that after a successful login and logout, valid credentials
    are still required
    """
    ui_login.login(username, password)
    assert not ui_login.is_logged_in(), (
        'Login unexpectedly succesful with invalid credentials')
    assert ui_login.errors, (
        'Expected login failure alert error(s) to be displayed')


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
def test_console_logo(CUSTOM_CONSOLE_LOGO, ui_login):
    """Verify that our custom console logo and its accompanying
    text display
    """

    assert ui.is_modal_notice_displayed, (
        'Expected modal notice to be displayed')
    import pdb; pdb.set_trace()
