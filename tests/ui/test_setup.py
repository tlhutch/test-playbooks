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


def check_card_titles(expected_card_titles, displayed_card_titles):
    """Check a list of displayed card titles against a list of expected titles
    """
    for expected_title in expected_card_titles:
        assert expected_title in displayed_card_titles, (
            'card with title {0} unexpectedly not displayed'.format(
                expected_title))

    for displayed_title in displayed_card_titles:
        assert displayed_title in expected_card_titles, (
            'card with title {0} unexpectedly displayed'.format(
                displayed_title))

    assert displayed_card_titles == expected_card_titles, (
        'unexpected card ordering: {0} != {1}'.format(
            displayed_card_titles, expected_card_titles))


def test_cards_route_to_expected_destination(ui_setup):
    """Verify succesful expected destination page load of setup menu cards
    """
    card_destinations = (
        (ui_setup.credentials_card, '/#/credentials'),
        (ui_setup.users_card, '/#/users'),
        (ui_setup.teams_card, '/#/teams'),
        (ui_setup.inventory_scripts_card, '/#/inventory_scripts'),
        (ui_setup.management_jobs_card, '/#/management_jobs'),
        (ui_setup.organizations_card, '/#/organizations'),
        (ui_setup.license_card, '/#/license'))

    for (card, dest) in card_destinations:
        assert card.is_displayed(), (
            'card with expected destination {0} not displayed'.format(dest))

        loaded_page = card.click()
        current_path = loaded_page._current_url.path

        assert dest in current_path, (
            '{0} unexpectedly not in current url path {1}'.format(
                dest, current_path))

        loaded_page.header.setup.click()


@pytest.mark.usefixtures('supported_window_sizes')
def test_card_visibility_and_ordering(ui_setup, anonymous_user, user_password):
    """Verify that the visibility and ordering of setup menu cards as an admin
    """
    admin_card_titles = [
        'CREDENTIALS',
        'USERS',
        'TEAMS',
        'ORGANIZATIONS',
        'MANAGEMENT JOBS',
        'INVENTORY SCRIPTS',
        'NOTIFICATIONS',
        'VIEW YOUR LICENSE',
        'ABOUT TOWER'
    ]

    check_card_titles(admin_card_titles, ui_setup.displayed_card_titles)

    anon_card_titles = [
        'CREDENTIALS',
        'USERS',
        'TEAMS',
        'ORGANIZATIONS',
        'INVENTORY SCRIPTS',
        'NOTIFICATIONS',
        'VIEW YOUR LICENSE',
        'ABOUT TOWER'
    ]

    with ui_setup.current_user(anonymous_user.username, user_password):
        check_card_titles(anon_card_titles, ui_setup.displayed_card_titles)


def test_dashboard_link(ui_setup):
    """Verify dashboard link visibility and behavior
    """
    assert ui_setup.dashboard_button.is_displayed(), (
        'Dashboard button unexpectedly not displayed')

    assert ui_setup.dashboard_button.is_clickable(), (
        'Dashboard button unexpectedly not clickable')

    dashboard = ui_setup.dashboard_button.click()

    assert 'home' in dashboard.current_url.lower(), (
        'Unexpected url content after clicking dashboard link')
