from itertools import combinations
import urlparse

import pytest

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

    assert ui.username.is_displayed(), (
        'Username input region unexpectedly not displayed')

    assert ui.resources.is_displayed(), (
        'Resources input region unexpectedly not displayed')

    assert ui.related_resources.is_displayed(), (
        'Related input region unexpectedly not displayed')

    search_locations = (ui.username, ui.resources, ui.related_resources)

    for (region, other_region) in combinations(search_locations, 2):
        assert not region.overlaps_with(other_region), (
            'Search regions unexpectedly overlapping')

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


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1072')
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
