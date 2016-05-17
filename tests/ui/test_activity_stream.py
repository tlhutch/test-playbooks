import json
import urlparse

import fauxfactory
import pytest

from common.utils import random_utf8_string


pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive
]


@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
    'supported_window_sizes'
)
def test_component_visibility_(ui_activity_stream):
    """Verify basic component visibility, page layout, and responsiveness
    """
    ui = ui_activity_stream

    assert ui.current_crumb == 'activity stream', (
        'unexpected breadcrumb displayed')

    assert ui.nav_dropdown.is_displayed(), (
        'Navigation dropdown region unexpectedly not displayed')

    assert not ui.panel.badge.is_displayed(), (
        'List panel badge unexpectedly displayed')

    assert ui.panel.surrounds(ui.nav_dropdown), (
        'Navigation dropdown not completely surrounded by list panel')


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1073')
@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
    'maximized_window_size'
)
def test_navigation_dropdown(ui_activity_stream, anonymous_user, user_password):
    """Verify expected functionality of the navigation dropdown widget
    """
    assert ui_activity_stream.nav_dropdown.selected_option == 'All Activity', (
        'Unexpected default value displayed for navigation dropdown')

    expected_nav_options = [
        'All Activity',
        'Credentials',
        'Hosts',
        'Inventories',
        'Inventory Scripts',
        'Job Templates',
        'Management Jobs',
        'Organizations',
        'Projects',
        'Schedules',
        'Teams',
        'Users'
    ]

    assert ui_activity_stream.nav_dropdown.options == expected_nav_options, (
        'Unexpected activity stream navigation dropdown select options')

    with ui_activity_stream.current_user(
            anonymous_user.username, user_password):

        # expected_anon_options = expected_nav_options[::]
        # expected_anon_options.remove('Management Jobs')

        expected_anon_options = expected_nav_options

        nav_options = ui_activity_stream.nav_dropdown.options

        assert nav_options == expected_anon_options, (
            'Unexpected activity stream navigation dropdown select options')

    for option in ui_activity_stream.nav_dropdown.options:
        ui_activity_stream.nav_dropdown.select(option)

        selected_option = ui_activity_stream.nav_dropdown.selected_option

        assert selected_option == option, (
            'Navigation option {0} unexpectedly unselected'.format(option))

        subtitle = ui_activity_stream.subtitle.text.lower()

        assert selected_option.lower() in subtitle, (
            'Unexpected stream subtitle {0} given selected option {1}'.format(
                subtitle, selected_option))

    # check that a non-default option remains selected after refreshing
    non_default = 'Organizations'
    ui_activity_stream.nav_dropdown.select(non_default)

    assert ui_activity_stream.nav_dropdown.selected_option == non_default, (
        'Navigation option {0} unexpectedly unselected'.format(non_default))

    ui_activity_stream.refresh()

    assert ui_activity_stream.nav_dropdown.selected_option == non_default, (
        'Navigation option {0} unexpectedly unselected'.format(non_default))


@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
)
def test_navigation_with_edit_query_params(ui_inventories_edit):
    """Verify expected activity stream functionality with url query parameters
    generated when linking from a crud edit page
    """
    expected_subtitle = ui_inventories_edit.details.title.text
    expected_id = str(ui_inventories_edit.kwargs.get('index'))

    activity_stream = ui_inventories_edit.activity_stream_link.click()

    assert 'activity_stream' in activity_stream.current_url, (
        '"activity_stream" unexpectedly not contained in current page url')

    assert activity_stream.nav_dropdown.selected_option == 'Inventories', (
        'Unexpected default value displayed for navigation dropdown')

    assert activity_stream.subtitle.is_displayed(), (
        'Activity stream subtitle unexpectedly not displayed')

    assert expected_subtitle in activity_stream.subtitle.text, (
        'Unexpected activity stream subtitle text')

    query = urlparse.parse_qs(activity_stream._current_url.query)

    assert query == {'target': ['inventory'], 'id': [expected_id]}, (
        'Unexpected activity stream url query parameters after page load')

    activity_stream.nav_dropdown.select('Job Templates')
    query_nav_select = urlparse.parse_qs(activity_stream._current_url.query)

    assert query_nav_select == {'target': ['job_template']}, (
        'Unexpected activity stream url query parameters after nav select')


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
def test_activity_stream_after_inventory_update(ui_inventories_edit):
    """Verify displayed event details, routing, and page functionality when
    updating a crud page resource and clicking over to the activity stream.
    """
    new_inventory_name = random_utf8_string()

    # change the name of the inventory
    ui_inventories_edit.details.name.set_text(new_inventory_name)
    ui_inventories_edit.details.save.click()

    # navigate to the activity stream page
    activity_stream = ui_inventories_edit.activity_stream_link.click()

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
        assert text.lower() in top_row['action'].text.lower(), (
            '{0} not found in top row action column'.format(text))


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1179')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
def test_event_details_modal_visibility(inventory, ui_activity_stream):
    """Verify component visibility, layout, and responsiveness of the activity
    stream event details modal
    """
    # update the inventory
    inventory.patch(name=fauxfactory.gen_alphanumeric(length=100))

    # refresh the page and sort the table by event time in ascending order
    ui_activity_stream.refresh()
    ui_activity_stream.table.set_column_sort_order(('event_time', 'ascending'))

    # click open the details modal for the top row
    event_details = ui_activity_stream.table[0]['event_details'].click()
    event_details.wait_until_displayed()

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
