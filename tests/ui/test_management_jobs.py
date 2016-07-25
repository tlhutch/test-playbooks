'''
from itertools import combinations

import pytest

pytestmark = [
    pytest.mark.skip,
    pytest.mark.nondestructive
]


@pytest.mark.usefixtures('authtoken', 'install_basic_license', 'supported_window_sizes')
def test_component_visibility(anonymous_user, ui_management_jobs):
    """Verify basic component visibility, page layout, and responsiveness
    """
    assert ui_management_jobs.current_crumb == 'management jobs', (
        'unexpected breadcrumb displayed')

    management_cards = ui_management_jobs.cards

    assert len(management_cards) > 0, 'No management job cards detected'

    for card in management_cards:
        assert card.is_displayed(), (
            'Management card unexpectedly not displayed')

        assert card.launch.is_displayed(), (
            'Management card launch icon unexpectedly not displayed')

        assert card.launch.is_clickable(), (
            'Management card launch icon unexpectedly not clickable')

        assert card.title.is_displayed(), (
            'Management card title unexpectedly not displayed')

        assert card.schedule.is_displayed(), (
            'Management card schedule icon unexpectedly not displayed')

        assert card.schedule.is_clickable(), (
            'Management card schedule icon unexpectedly not clickable')

    # Take up to the first four cards displayed and verify that none
    # of them overlap or touch for any of the supported window sizes
    for (card, other_card) in combinations(management_cards[:4], 2):
        assert not card.overlaps_with(other_card), (
            'management card regions unexpectedly overlapping')


@pytest.mark.usefixtures('authtoken', 'install_basic_license', 'maximized_window_size')
def test_api_referential_integrity(api_system_job_templates_pg, ui_management_jobs):
    """Peform basic end-to-end read-only verification of loaded page content
    against data returned by the system job templates api
    """
    system_jobs = api_system_job_templates_pg.get().results
    management_cards = ui_management_jobs.cards

    assert len(management_cards) == len(system_jobs), (
        'Unexpected number of management job cards displayed')

    expected_titles = [job.json['name'].lower() for job in system_jobs]

    for card in management_cards:
        assert card.title.text.lower() in expected_titles, (
            'Unexpected management card title')


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1071')
@pytest.mark.usefixtures('authtoken', 'maximized_window_size')
def test_access_without_permission(non_superuser, user_password, ui_login):
    ui_dashboard = ui_login.login(non_superuser.username, user_password)

    target_url = ui_dashboard._current_url.replace(
        path='/#/management_jobs', query='').geturl()

    ui_dashboard.get(target_url)

    assert ui_dashboard.is_loaded(), 'Expected redirect to dashboard page'
'''