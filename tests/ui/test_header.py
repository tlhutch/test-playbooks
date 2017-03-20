import pytest
from selenium.common.exceptions import TimeoutException


pytestmark = [pytest.mark.ui]


@pytest.mark.usefixtures('supported_window_sizes')
def test_header_shows_correct_username(v1, ui, ui_user):
    """Verify correctly displayed username on header"""
    dashboard = ui.dashboard
    msg = 'Unable to verify correctly displayed username on header'

    expected = ui_user.username
    actual = dashboard.header.username

    assert expected.lower() == actual.lower(), msg
    with dashboard.current_user(ui_user.username, refresh=False):
        expected = ui_user.username
        actual = dashboard.header.username
        assert expected.lower() == actual.lower(), msg


@pytest.mark.usefixtures('supported_window_sizes')
def test_header_click_through(ui):
    """Verify header menu link functionality"""
    dashboard = ui.dashboard

    link_names = [
        'inventories',
        'jobs',
        'logo',
        'templates',
        'portal',
        'projects',
        'setup',
        'user',
    ]
    for name in link_names:
        getattr(dashboard.header, name).click()
        try:
            dashboard.wait.until(lambda _: name in dashboard.driver.current_url)
        except TimeoutException:
            pytest.fail('Unexpected destination url content')
        dashboard.header.logo.click()
        dashboard.wait_until_loaded()
