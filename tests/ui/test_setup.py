import pytest


pytestmark = [pytest.mark.ui]


def test_displayed_card_titles_and_ordering(ui, rando):
    """Verify that the visibility and ordering of setup menu cards
    as an admin and a random user
    """
    ui_setup = ui.setup_menu.get()

    admin_card_titles = [
        'ORGANIZATIONS',
        'USERS',
        'TEAMS',
        'CREDENTIALS',
        'MANAGEMENT JOBS',
        'INVENTORY SCRIPTS',
        'NOTIFICATIONS',
        'VIEW YOUR LICENSE',
        'CONFIGURE TOWER',
        'ABOUT TOWER',
    ]

    assert ui_setup.card_titles == admin_card_titles

    anon_card_titles = [
        'ORGANIZATIONS',
        'USERS',
        'TEAMS',
        'CREDENTIALS',
        # 'MANAGEMENT JOBS',
        'INVENTORY SCRIPTS',
        # 'NOTIFICATIONS',
        'VIEW YOUR LICENSE',
        # 'CONFIGURE TOWER',
        'ABOUT TOWER',
    ]

    with ui_setup.current_user(rando.username):
        ui_setup.wait_until_loaded()
        assert ui_setup.card_titles == anon_card_titles


def test_cards_route_to_expected_destination(ui):
    """Verify succesful expected link destination of setup menu cards"""
    ui_setup = ui.setup_menu.get()

    card_destinations = {
        'organizations': '/#/organizations',
        'users': '/#/users',
        'teams': '/#/teams',
        'credentials': '/#/credentials',
        'management jobs': '/#/management_jobs',
        'inventory scripts': '/#/inventory_script',
        'notifications': '/#/notification_templates',
        'view your license': '/#/license',
        'about tower': '/#/setup/about',
        'configure tower': '/#/configuration',
    }
    for card in ui_setup.cards:
        title_key = card.title.text.lower()
        expected_url_content = card_destinations[title_key]
        assert expected_url_content in card.href, (
            'Unexpected {0} link href: {1}'.format(card.title, card.href))
