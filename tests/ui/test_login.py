import pytest
from selenium.common.exceptions import TimeoutException


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='class')
def login_page(request, ui_client):
    yield ui_client.ui.login.get()
    ui_client.browser.quit()


def test_login_logout(login_page, default_tower_credentials):
    """Verify a successful login and logout with default credentials"""
    username = default_tower_credentials['username']
    password = default_tower_credentials['password']
    try:
        login_page.login_with_enter_key(username, password)
    except TimeoutException:
        pytest.fail('Unable to verify a successful login')
    try:
        login_page.logout()
    except TimeoutException:
        pytest.fail('Unable to verify a successful logout')


@pytest.mark.parametrize('username,password', [
    ('wrosellini', 'quintus'),
    ('wrosellini', ''),
    ('', 'quintus'),
    ('', '')
])
def test_login_invalid_credentials(login_page, username, password):
    """Verify that after a successful login and logout, valid credentials
    are still required
    """
    login_page.login(username, password)
    assert not login_page.is_logged_in(), (
        'Login unexpectedly succesful with invalid credentials')
    assert login_page.errors, (
        'Expected login failure alert error(s) to be displayed')


@pytest.mark.github('https://github.com/ansible/tower-qa/issues/782')
def test_stock_branding(login_page):
    """Verify our stock login modal branding and notice"""
    image_src = login_page.modal_image.get_attribute('src')
    assert image_src.endswith('/static/assets/tower-logo-login.svg'), \
        "Unexpected console_logo path."
    assert not login_page.is_modal_notice_displayed(), (
        'Expected modal notice to not be displayed')


@pytest.mark.github('https://github.com/ansible/tower-qa/issues/782')
def test_custom_rebranding(login_page, CUSTOM_CONSOLE_LOGO):
    """Verify that our login modal may be rebranded with a custom
    image and notice
    """
    image_src = login_page.modal_image.get_attribute('src')
    assert image_src.endswith('/static/assets/custom_console_logo.png'), \
        "Unexpected console_logo path."
    assert login_page.is_modal_notice_displayed(), (
        'Expected modal notice to be displayed')
