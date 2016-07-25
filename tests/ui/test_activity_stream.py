import json
import urlparse

import fauxfactory
import pytest

from common.utils import random_utf8


pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.skip,
    pytest.mark.usefixtures(
        'module_install_enterprise_license',
        'max_window'
    )
]


@pytest.mark.usefixtures('supported_window_sizes')
def test_component_visibility_(ui_activity_stream):
    """Verify basic component visibility, page layout, and responsiveness
    """
    assert ui_activity_stream.current_crumb == 'activity stream', (
        'unexpected breadcrumb displayed')
    assert ui_activity_stream.navigation_dropdown.is_displayed(), (
        'Navigation dropdown region unexpectedly not displayed')
    assert not ui_activity_stream.panel.badge.is_displayed(), (
        'List panel badge unexpectedly displayed')
    assert ui_activity_stream.panel.surrounds(
        ui_activity_stream.navigation_dropdown), (
            'Navigation dropdown not completely surrounded by list panel')


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1073')
def test_navigation_dropdown(ui_activity_stream, anonymous_user, user_password):
    """Verify expected functionality of the navigation dropdown widget
    """
    assert ui_activity_stream.navigation_dropdown.get_value() == 'All Activity', (
        'Unexpected default value displayed for navigation dropdown')

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
        'Users'
    ]
    assert ui_activity_stream.navigation_dropdown.get_value() == expected_nav_options, (
        'Unexpected activity stream navigation dropdown select options')

    for option in ui_activity_stream.navigation_dropdown.get_value():
        ui_activity_stream.navigation_dropdown.set_value(option)
        selected_option = ui_activity_stream.navigation_dropdown.get_value()
        assert selected_option == option, (
            'Navigation option {0} unexpectedly unselected'.format(option))

        subtitle = ui_activity_stream.list_subtitle.text.lower()
        assert selected_option.lower() in subtitle, (
            'Unexpected stream subtitle {0} given selected option {1}'.format(
                subtitle, selected_option))

    # check that a non-default option remains selected after refreshing
    non_default = 'Organizations'
    ui_activity_stream.navigation_dropdown.set_value(non_default)
    assert ui_activity_stream.navigation_dropdown.get_value() == non_default, (
        'Navigation option {0} unexpectedly unselected'.format(non_default))
    ui_activity_stream.refresh()
    assert ui_activity_stream.navigation_dropdown.get_value() == non_default, (
        'Navigation option {0} unexpectedly unselected'.format(non_default))


def test_navigation_with_edit_query_params(ui_inventory_edit):
    """Verify expected activity stream functionality with url query parameters
    generated when linking from a crud edit page
    """
    expected_subtitle = ui_inventory_edit.details.title.text
    expected_id = str(ui_inventory_edit.kwargs.get('id'))

    activity_stream = ui_inventory_edit.activity_stream_link.click()

    assert 'activity_stream' in activity_stream.driver.current_url, (
        '"activity_stream" unexpectedly not contained in current page url')
    assert activity_stream.navigation_dropdown.get_value() == 'Inventories', (
        'Unexpected default value displayed for navigation dropdown')
    assert activity_stream.list_subtitle.is_displayed(), (
        'Activity stream subtitle unexpectedly not displayed')
    assert expected_subtitle in activity_stream.list_subtitle.text, (
        'Unexpected activity stream subtitle text')

    query = urlparse.parse_qs(activity_stream._current_url.query)
    assert query == {'target': ['inventory'], 'id': [expected_id]}, (
        'Unexpected activity stream url query parameters after page load')

    activity_stream.navigation_dropdown.set_value('Job Templates')
    query_nav_select = urlparse.parse_qs(activity_stream._current_url.query)
    assert query_nav_select == {'target': ['job_template']}, (
        'Unexpected activity stream url query parameters after nav select')


def test_activity_stream_after_inventory_update(ui_inventory_edit):
    """Verify displayed event details, routing, and page functionality when
    updating a crud page resource and clicking over to the activity stream.
    """
    new_inventory_name = random_utf8()
    # change the name of the inventory
    ui_inventory_edit.details.name.set_text(new_inventory_name)
    ui_inventory_edit.details.save.click()
    # navigate to the activity stream page
    activity_stream = ui_inventory_edit.activity_stream_link.click()
    # verify we have at least one event in our activity stream
    assert len(activity_stream.table.rows) > 0, (
        'Activity stream table unexpectedly not populated')
    # sort the table by event time in ascending order
    activity_stream.table.set_column_sort_order(('time', 'ascending'))
    # get the top row
    top_row = activity_stream.table[0]
    # verify the top row mentions an inventory update and the inventory name
    expected_text = ('inventory', 'update', new_inventory_name)
    for text in expected_text:
        assert text.lower() in top_row.action.text.lower(), (
            '{0} not found in top row action column'.format(text))


def test_event_details_modal(factories, ui_activity_stream):
    """Verify component visibility, layout, and responsiveness of the activity
    stream event details modal
    """
    # make some test data
    inventory = factories.inventory()
    # update the inventory
    inventory.patch(name=fauxfactory.gen_alphanumeric(length=100))
    # refresh the page and sort the table by event time in ascending order
    ui_activity_stream.driver.refresh()
    ui_activity_stream.wait_until_loaded()
    ui_activity_stream.table.header.set_sort_status(('time', 'ascending'))
    # click open the details modal for the top row
    event_details = ui_activity_stream.table[0].open_details()

    assert event_details.close.is_clickable(), (
        'Event details close button unexpectedly not clickable')
    assert event_details.ok.is_clickable(), (
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
