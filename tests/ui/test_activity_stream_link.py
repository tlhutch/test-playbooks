import urlparse

import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures('maximized_window_size')
]

# These states are expected to have fully-functional activity stream links
# when the activity stream feature is enabled
_pages_with_activity_stream = [
    'ui_credentials',
    'ui_credentials_add',
    'ui_credentials_edit',
    'ui_dashboard',
    'ui_hosts',
    'ui_inventories',
    'ui_inventories_add',
    'ui_inventories_edit',
    'ui_inventory_scripts',
    'ui_inventory_scripts_add',
    'ui_inventory_scripts_edit',
    'ui_job_templates',
    'ui_job_templates_add',
    'ui_management_jobs',
    'ui_organizations',
    'ui_organizations_add',
    'ui_organizations_edit',
    'ui_projects',
    'ui_projects_add',
    'ui_projects_edit',
    'ui_teams',
    'ui_teams_add',
    'ui_teams_edit',
    'ui_users',
    'ui_users_add',
    'ui_users_edit'
]

_pages_with_xfails = [

    pytest.mark.xfail(
        'ui_job_templates_schedule',
        reason='https://github.com/ansible/ansible-tower/issues/919'),

    pytest.mark.xfail(
        'ui_projects_schedule',
        reason='https://github.com/ansible/ansible-tower/issues/919'),

    pytest.mark.xfail(
        'ui_job_templates_edit',
        reason='https://github.com/ansible/ansible-tower/issues/919'),
]


@pytest.fixture(params=_pages_with_activity_stream + _pages_with_xfails)
def page_with_activity_stream(request):
    if 'ui_organizations' in request.param:
        if 'install_basic_license' in request.node.fixturenames:
            pytest.skip('basic license precludes organization page fixtures')
    return request.getfuncargvalue(request.param)


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
def test_activity_stream_link_with_enterprise_license(page_with_activity_stream):
    """Verify activity stream link visibility and behavior with an
    enterprise license
    """
    assert page_with_activity_stream.activity_stream_link.is_displayed(), (
        'Activity stream link unexpectedly not displayed')

    assert page_with_activity_stream.activity_stream_link.is_clickable(), (
        'Activity stream link unexpectedly not clickable')

    crumb = page_with_activity_stream.current_crumb

    activity_stream = page_with_activity_stream.activity_stream_link.click()

    assert 'activity_stream' in activity_stream.current_url, (
        '"activity_stream" unexpectedly not contained in current page url')

    assert activity_stream.subtitle.is_displayed(), (
        'activity stream subtitle unexpectedly not displayed')

    if crumb != 'dashboard':
        query = urlparse.parse_qs(activity_stream._current_url.query)
        assert 'target' in query, (
            'target key unexpectedly not found in url query parameters')


@pytest.mark.usefixtures('authtoken', 'install_basic_license')
def test_activity_stream_link_with_basic_license(page_with_activity_stream):
    """Verify activity stream link visibility and behavior with a basic
    license
    """
    assert not page_with_activity_stream.activity_stream_link.is_displayed(), (
        'Activity stream link unexpectedly displayed')

    assert not page_with_activity_stream.activity_stream_link.is_clickable(), (
        'Activity stream link unexpectedly clickable')
