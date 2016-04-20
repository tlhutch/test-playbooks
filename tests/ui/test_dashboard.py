import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_basic_license',
        'maximized_window_size'
    )
]


@pytest.mark.usefixtures('supported_window_sizes')
def test_page_layout(ui_dashboard):
    """Verify page component visibility
    """
    assert ui_dashboard.job_templates.is_displayed(), (
        'Unable to locate job templates panel')

    assert ui_dashboard.jobs.is_displayed(), (
        'Unable to locate job panel')

    assert ui_dashboard.job_status_toolbar.is_displayed(), (
        'Unable to locate job status toolbar')

    assert not ui_dashboard.has_clock_button(), (
        'Old style activity stream button unexpectedly displayed')


def test_job_status_toolbar_dropdowns(ui_dashboard):
    """Verify expected behavior of job status toolbar dropdown menus
    """
    toolbar = ui_dashboard.job_status_toolbar

    dropdowns = (
        ('period', toolbar.period_dropdown),
        ('job_types', toolbar.job_types_dropdown),
        ('status', toolbar.status_dropdown))

    for (name, dd) in dropdowns:
        for option in dd.options:

            msg = 'job status toolbar {0} dropdown'.format(name)

            assert dd.is_displayed(), (
                'Expected {0} to be displayed'.format(msg))

            dd.select(option)
            selected_option = dd.selected_option

            assert selected_option == option, (
                'Unexpected {0} value: {1} != {2}'.format(msg, selected_option, option))

            assert dd.is_displayed(), (
                'Expected {0} to be displayed'.format(msg))

            selected_option = dd.selected_option

            assert selected_option == option, (
                'Unexpected {0} value: {1} != {2}'.format(msg, selected_option, option))
