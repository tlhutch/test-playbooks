import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_basic_license',
        'maximized_window_size'
    )
]


def test_header_displays_correct_username(ui_dashboard, anonymous_user,
                                          user_password, default_credentials):
    """Verify correctly displayed username on header
    """
    default_un = default_credentials['username']

    assert ui_dashboard.header.user == default_un, (
        'Unable to verify correctly displayed username on header')

    with ui_dashboard.current_user(anonymous_user.username, user_password):
        assert ui_dashboard.header.user == anonymous_user.username.lower(), (
            'Unable to verify that the header displays the correct username')


@pytest.mark.usefixtures('supported_window_sizes')
def test_header_menu_item_visibility(ui_dashboard):
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


@pytest.mark.usefixtures('supported_window_sizes')
def test_header_links(ui_dashboard):
    """Verify header menu links route to the expected page when clicked
    """
    header = ui_dashboard.header

    header.jobs_link.click()
    assert 'jobs' in ui_dashboard._current_url.path, (
        'Expected jobs_link in url after clicking header jobs link ')
    header.logo.click()

    header.user_link.click()
    assert 'users' in ui_dashboard._current_url.path, (
        'Expected users in url after clicking header user link')
    header.logo.click()

    header.setup_link.click()
    assert 'setup' in ui_dashboard._current_url.path, (
        'Expected setup in url after clicking header setup link')
    header.logo.click()

    header.job_templates_link.click()
    assert 'job_templates' in ui_dashboard._current_url.path, (
        'Expected job_templates in url after clicking header job templates link')
    header.logo.click()

    header.projects_link.click()
    assert 'projects' in ui_dashboard._current_url.path, (
        'Expected projects in url after clicking header projects link')
    header.logo.click()

    header.inventories_link.click()
    assert 'inventories' in ui_dashboard._current_url.path, (
        'Expected inventories in url after clicking header inventories link')
    header.logo.click()

    assert 'home' in ui_dashboard._current_url.path, (
        'Expected home in url after clicking header logo link')
