import json

import fauxfactory
import pytest


pytestmark = [pytest.mark.ui]


def test_toggle_all_users_visble_to_org_admin(v1, ui, org_admin, rando):
    """Verify functionality of org admin user visibility setting"""
    configuration, users = ui.configuration, ui.users

    configuration.get()
    configuration.system.misc.org_admins_can_see_all_users.value = False

    with users.get().current_user(org_admin.username):
        users.search(rando.username)
        users.wait_until_loaded()
        assert users.passively_wait_until(lambda: users.badge.text == '0')

    configuration.get()
    configuration.system.misc.org_admins_can_see_all_users.value = True

    with users.get().current_user(org_admin.username):
        users.search(rando.username)
        assert users.passively_wait_until(lambda: users.badge.text == '1')


def test_configure_tower_settings_card_not_visble_to_org_admin(v1, ui, org_admin):
    """Check expected visbility of settings page configure tower card
    for superusers and org admins
    """
    settings = ui.setup_menu.get()

    assert 'CONFIGURE TOWER' in settings.card_titles

    with settings.current_user(org_admin.username):
        assert 'CONFIGURE TOWER' not in settings.card_titles


def test_activity_stream_toggle(v1, ui, inventory):
    """Verify that activity stream events are not displayed for events that
    occur while activity stream logging is disabled from configuration menu.
    """
    configuration, activity_stream = ui.configuration, ui.activity_stream
    names = (inventory.name, fauxfactory.gen_alphanumeric(), fauxfactory.gen_alphanumeric())
    # patch the inventory with activity reporting enabled
    configuration.get()
    configuration.system.activity_stream.activity_stream_enabled.value = True
    inventory.patch(name=names[1])
    # patch the inventory with activity reporting disabled
    configuration.system.activity_stream.activity_stream_enabled.value = False
    inventory.patch(name=names[2])
    # re-enable activity reporting
    configuration.system.activity_stream.activity_stream_enabled.value = True
    # load the activity stream
    activity_stream.get()
    activity_stream.navigation_dropdown.value = 'Inventories'
    # get any row mentioning the updated inventory names
    results = activity_stream.table.query(lambda r: any(n in r.action.text for n in names[1:]))
    # there should be exactly one result
    assert len(results) == 1
    # scrape event change data for the result
    changes = json.loads(results.pop().open_details().changes.text)
    # our one result should reference the name[0] -> name[1] event
    assert changes == {"name": [names[0], names[1]]}
