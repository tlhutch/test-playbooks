from itertools import combinations

import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.ui_debug,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
        'max_window',
    )
]


def test_component_visibility(ui_management_jobs):
    """Verify basic component visibility, page layout, and responsiveness
    """
    assert ui_management_jobs.current_breadcrumb == 'management jobs', (
        'unexpected breadcrumb displayed')

    management_cards = ui_management_jobs.cards

    assert len(management_cards) > 0, 'No management job cards detected'

    for card in management_cards:
        assert card.is_displayed(), (
            'Management card unexpectedly not displayed')
        assert card.launch.is_displayed(), (
            'Management card launch icon unexpectedly not displayed')
        assert card.launch.is_enabled(), (
            'Management card launch icon unexpectedly not clickable')
        assert card.title.is_displayed(), (
            'Management card title unexpectedly not displayed')
        assert card.schedule.is_displayed(), (
            'Management card schedule icon unexpectedly not displayed')
        assert card.schedule.is_enabled(), (
            'Management card schedule icon unexpectedly not clickable')
    # Take up to the first four cards displayed and verify that none
    # of them overlap or touch for any of the supported window sizes
    for (card, other_card) in combinations(management_cards[:4], 2):
        assert not card.overlaps_with(other_card), (
            'management card regions unexpectedly overlapping')


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
