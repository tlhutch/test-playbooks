import json

import fauxfactory
import pytest


pytestmark = [pytest.mark.ui]


@pytest.mark.usefixtures('supported_window_sizes')
def test_component_visibility(ui):
    """Verify basic component visibility, page layout, and responsiveness
    """
    activity = ui.activity_stream.get()
    assert activity.current_breadcrumb == 'activity stream'
    assert activity.navigation_dropdown.is_displayed()
    assert activity.list_panel.surrounds(activity.navigation_dropdown)


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4406')
def test_navigation_dropdown(ui):
    """Verify expected functionality of the navigation dropdown widget
    """
    expected_nav_options = [
        'All Activity',
        'Credentials',
        'Hosts',
        'Inventories',
        'Inventory Scripts',
        'Job Templates',
        'Jobs',
        'Organizations',
        'Projects',
        'Schedules',
        'Teams',
        'Users',
    ]
    activity = ui.activity_stream.get()
    assert activity.navigation_dropdown.value == 'All Activity', (
        'Unexpected default nav option')
    # check nav options
    options = activity.navigation_dropdown.options
    assert options == expected_nav_options
    for opt in options:
        activity.navigation_dropdown.value = opt
        selected = activity.navigation_dropdown.value
        assert selected == opt
        assert activity.subtitle_text_eventually_contains(selected)
    # check that a non-default option remains selected after refreshing
    nondefault = 'Organizations'
    activity.navigation_dropdown.value = nondefault
    assert activity.navigation_dropdown.value == nondefault
    ui.activity_stream.driver.refresh()
    ui.activity_stream.wait_until_loaded()
    assert activity.navigation_dropdown.value == nondefault


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4185')
def test_navigation_with_edit_query_params(ui, inventory):
    """Verify expected activity stream functionality with url query parameters
    generated when linking from a crud edit page
    """
    inventory_edit = ui.inventory_edit.get(id=inventory.id)
    expected_subtitle = inventory_edit.details.title.text.lower()

    activity_stream = inventory_edit.open_activity_stream()

    assert activity_stream.navigation_dropdown.value == 'Inventories', (
        'Unexpected default value displayed for navigation dropdown')
    assert expected_subtitle in activity_stream.list_subtitle.text.lower(), (
        'Unexpected activity stream subtitle text')
    assert 'target=inventory' in activity_stream.driver.current_url, (
        'Unexpected activity stream url content after page load')

    activity_stream.navigation_dropdown.value = 'Job Templates'
    assert 'target=job_template' in activity_stream.driver.current_url, (
        'Unexpected activity stream url query content after nav select')


def test_activity_stream_after_inventory_update(ui, inventory):
    """Verify displayed event details, routing, and page functionality when
    updating a crud page resource and clicking over to the activity stream.
    """
    inventory_edit = ui.inventory_edit.get(id=inventory.id)
    new_name = fauxfactory.gen_alphanumeric()
    # change the name of the inventory
    inventory_edit.details.name.value = new_name
    inventory_edit.details.save.click()
    inventory_edit.table.wait_for_table_to_load()
    # navigate to the activity stream page
    inventory_edit.details.scroll_save_into_view()
    activity_stream = inventory_edit.open_activity_stream()
    # verify we have at least one event in our activity stream
    assert len(activity_stream.table.rows) > 0, (
        'Activity stream table unexpectedly not populated')
    # sort the table by event time in ascending order
    activity_stream.table.header.set_sort_status(('time', 'ascending'))
    # verify the top row mentions an inventory update and the inventory name
    action_text = activity_stream.table.rows[0].action.text
    assert 'inventory' in action_text
    assert 'update' in action_text
    assert new_name in action_text


def test_event_details_modal(ui, inventory):
    """Verify component visibility, layout, and responsiveness of the activity
    stream event details modal
    """
    # update the inventory
    inventory.patch(name=fauxfactory.gen_alphanumeric(length=100))
    # open the activity stream and sort the table by event time in ascending order
    activity_stream = ui.activity_stream.get()
    activity_stream.navigation_dropdown.value = 'Inventories'
    activity_stream.table.header.set_sort_status(('time', 'ascending'))
    # click open the details modal for the top row
    event_details = activity_stream.table.rows[0].open_details()
    assert event_details.close.is_enabled(), (
        'Event details close button unexpectedly not clickable')
    assert event_details.ok.is_enabled(), (
        'Event details ok button unexpectedly not clickable')
    assert event_details.changes.is_displayed(), (
        'Changes information unexpectedly not displayed')
    # verify the displayed changes detail text is valid json
    try:
        json.loads(event_details.changes.text)
    except ValueError:
        pytest.fail('Unable to verify displayed change text is valid json')
    # verify user and operation details regions are fully surrounded by the
    # modal window
    assert event_details.surrounds(event_details.initiated_by), (
        'User details not fully surrounded by event details modal')
    assert event_details.surrounds(event_details.operation), (
        'Operation details not fully surrounded by event details modal')
