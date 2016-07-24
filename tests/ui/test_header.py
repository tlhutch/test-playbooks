import pytest
from selenium.common.exceptions import TimeoutException


pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
        'supported_window_sizes',
    )
]


def test_header_shows_correct_username(
        ui_user_credentials, ui_dashboard, factories):
    """Verify correctly displayed username on header
    """
    msg = 'Unable to verify correctly displayed username on header'

    expected = ui_user_credentials['username']
    actual = ui_dashboard.header.username

    assert expected.lower() == actual.lower(), msg

    anon_user = factories.user()

    with ui_dashboard.current_user(anon_user.username):
        expected = anon_user.username
        actual = ui_dashboard.header.username
        assert expected.lower() == actual.lower(), msg


def test_header_click_through(ui_dashboard):
    """Verify header menu link functionality
    """
    link_names = (
        'inventories',
        'jobs',
        'job_templates',
        'portal',
        'projects',
        'setup',
        'user'
    )
    for link_name in link_names:
        getattr(ui_dashboard.header, link_name).click()
        check_url = lambda _: link_name in ui_dashboard.driver.current_url
        try:
            ui_dashboard.wait.until(check_url)
        except TimeoutException:
            pytest.fail('Unexpected destination url content')
        ui_dashboard.header.logo.click()
        ui_dashboard.wait_until_loaded()
