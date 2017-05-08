import urlparse

import pytest
import requests
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


def test_third_party_auth_icon(login_page, authtoken, sso_settings_pg, configure_auth):
    """Verify that third-party auth icons appear after API configuration."""
    # sso icons should not be initially present
    assert not login_page.sso_icons, \
        "Login page sso icons displayed before initial configuration."
    # configure sso endpoint
    configure_auth(sso_settings_pg)
    login_page.driver.refresh()
    login_page.wait_until_loaded_with_auth_icon()
    # check for new icon
    assert len(login_page.sso_icons) == 1, \
        "Unexpected number of sso icons found."
    # check that we have our expected icon
    if "azuread-oauth2/" in sso_settings_pg.endpoint:
        assert login_page.is_azuread_icon_displayed()
    elif "github/" in sso_settings_pg.endpoint:
        assert login_page.is_github_icon_displayed()
    elif "github-org/" in sso_settings_pg.endpoint:
        assert login_page.is_github_org_icon_displayed()
    elif "github-team/" in sso_settings_pg.endpoint:
        assert login_page.is_github_team_icon_displayed()
    elif "google-oauth2/" in sso_settings_pg.endpoint:
        assert login_page.is_google_icon_displayed()
    else:
        raise ValueError("Received unhandled settings page.")


def test_stock_branding(login_page):
    """Verify our stock login modal branding and notice"""
    image_src = login_page.modal_image.get_attribute('src')
    assert image_src.endswith('/static/assets/tower-logo-login.svg'), \
        "Unexpected console_logo path."
    assert not login_page.is_modal_notice_displayed(), (
        'Expected modal notice to not be displayed')


def test_custom_rebranding(login_page, authtoken, install_custom_branding):
    """Verify that our login modal may be rebranded with a custom
    image and notice.
    """
    login_page.driver.refresh()
    login_page.wait_until_loaded_with_modal_notice()
    image_src = login_page.modal_image.get_attribute('ng-src')
    assert image_src.startswith('data:image')
    assert login_page.is_modal_notice_displayed(), (
        'Expected modal notice to be displayed')


def test_token_invalidation_on_logout(ui, base_url):
    """Verify tokens are invalidated on logout"""
    # get client cookie store
    cookies = {str(c['name']): str(c['value']) for c in ui.dashboard.driver.get_cookies()}
    # get auth token from client cookie store
    token = 'Token ' + cookies['token'].replace('%22', '')
    # get the browser's user agent
    agent = str(ui.dashboard.driver.execute_script('return navigator.userAgent;'))
    # logout through the header menu
    ui.dashboard.header.logout.click()
    ui.login.wait_until_loaded()
    # make an http request to a restricted endpoint using the grifted browser
    # credentials
    url = urlparse.urljoin(base_url, '/api/v1/settings/')
    headers = {
        'Authorization': token,
        'User-Agent': agent,
        'Content-Type': 'application/json',
    }
    response = requests.get(url, cookies=cookies, headers=headers, verify=False)
    assert response.status_code == 401
