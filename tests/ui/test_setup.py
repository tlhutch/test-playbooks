import pytest
 

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
        'max_window',
    )
]


# -----------------------------------------------------------------------------
# Assertion Helpers and Utilities
# -----------------------------------------------------------------------------


def check_card_titles(expected_titles, displayed_titles):
    """Check a list of displayed card titles against a list of expected titles
    """
    msg_fail = '{0} != {1}'.format(expected_titles, displayed_titles)
    assert all([dt in expected_titles for dt in displayed_titles]), (
        'card title(s) unexpectedly displayed: ' + msg_fail)
    assert all([et in displayed_titles for et in expected_titles]), (
        'card title(s) unexpectedly not displayed: ' + msg_fail)
    assert expected_titles == displayed_titles, (
        'unexpected card ordering: ' + msg_fail)


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_displayed_card_titles_and_ordering(factories, ui_setup):
    """Verify that the visibility and ordering of setup menu cards as an admin
    """
    admin_card_titles = [
        'ORGANIZATIONS',
        'USERS',
        'TEAMS',
        'CREDENTIALS',
        'MANAGEMENT JOBS',
        'INVENTORY SCRIPTS',
        'NOTIFICATIONS',
        'VIEW YOUR LICENSE',
        'ABOUT TOWER'
    ]
    check_card_titles(admin_card_titles, ui_setup.card_titles)

    anon_card_titles = [
        'ORGANIZATIONS',
        'USERS',
        'TEAMS',
        'CREDENTIALS',
        #'MANAGEMENT JOBS',
        'INVENTORY SCRIPTS',
        #'NOTIFICATIONS',
        'VIEW YOUR LICENSE',
        'ABOUT TOWER'
    ]
    anon = factories.user()
    with ui_setup.current_user(anon.username):
        ui_setup.wait_until_loaded()
        check_card_titles(anon_card_titles, ui_setup.card_titles)


def test_cards_route_to_expected_destination(ui_setup):
    """Verify succesful expected link destination of setup menu cards
    """
    card_destinations = {
        'organizations': '/#/organizations',
        'users': '/#/users',
        'teams': '/#/teams',
        'credentials': '/#/credentials',
        'management jobs': '/#/management_jobs',
        'inventory scripts': '/#/inventory_scripts',
        'notifications': '/#/notification_templates',
        'view your license': '/#/license',
        'about tower': '/#/setup/about'
    }
    for card in ui_setup.cards:
        title_key = card.title.text.lower()
        expected_url_content = card_destinations[title_key]
        assert expected_url_content in card.href, (
            'Unexpected {0} link href: {1}'.format(card.title, card.href))
