from itertools import combinations

import pytest


pytestmark = [pytest.mark.ui]


@pytest.mark.usefixtures('supported_window_sizes')
def test_component_visibility(ui):
    """Verify basic component visibility, page layout, and responsiveness
    """
    mgmt = ui.management_jobs.get()

    assert mgmt.current_breadcrumb == 'management jobs', (
        'unexpected breadcrumb displayed')

    mgmt.wait.until(lambda _: mgmt.cards)
    mgmt_cards = mgmt.cards

    assert len(mgmt_cards) > 0, 'No management job cards detected'

    for card in mgmt_cards:
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
    for (card, other_card) in combinations(mgmt_cards[:4], 2):
        assert not card.overlaps(other_card), (
            'management card regions unexpectedly overlapping')


def test_api_referential_integrity(v1, ui):
    """Peform basic end-to-end read-only verification of loaded page content
    against data returned by the system job templates api
    """
    sysjobs = v1.system_job_templates.get().results

    mgmt = ui.management_jobs.get()

    mgmt.wait.until(lambda _: mgmt.cards)
    mgmt_cards = mgmt.cards

    assert len(mgmt_cards) == len(sysjobs), (
        'Unexpected number of management job cards displayed')

    expected_titles = [j.json['name'].lower() for j in sysjobs]

    for card in mgmt_cards:
        assert card.title.text.lower() in expected_titles, (
            'Unexpected management card title')
