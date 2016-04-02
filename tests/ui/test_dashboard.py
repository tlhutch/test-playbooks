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
    assert ui_dashboard.job_status_graph_tab.is_displayed(), (
        'Unable to locate dashboard job status graph tab')

    assert ui_dashboard.host_status_graph_tab.is_displayed(), (
        'Unable to locate dashboard host status graph tab')

    assert ui_dashboard.host_status_graph.is_displayed(), (
        'Unable to locate host status graph')

    assert ui_dashboard.job_status_graph.is_displayed(), (
        'Unable to locate job status graph')

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
        ('job_types', toolbar.job_types_dropdown))

    for (name, dd) in dropdowns:
        for option in dd.options:

            msg = 'job status toolbar {0} dropdown'.format(name)

            assert dd.is_displayed(), (
                'Expected {0} to be displayed'.format(msg))

            dd.select(option)
            selected_option = dd.selected_option

            assert selected_option == option, (
                'Unexpected {0} value: {1} != {2}'.format(msg, selected_option, option))

            ui_dashboard.host_status_graph_tab.click()
            ui_dashboard.job_status_graph_tab.click()

            assert dd.is_displayed(), (
                'Expected {0} to be displayed'.format(msg))

            selected_option = dd.selected_option

            assert selected_option == option, (
                'Unexpected {0} value: {1} != {2}'.format(msg, selected_option, option))


def test_job_status_toolbar_status_buttons(ui_dashboard):
    toolbar = ui_dashboard.job_status_toolbar

    toolbar.fail_status_button.enable()
    toolbar.success_status_button.enable()

    assert toolbar.fail_status_button.is_enabled(), (
        'Expected fail status button to be enabled after enabling '
        'success status button then enabling fail status button')

    assert toolbar.success_status_button.is_enabled(), (
        'Expected success status button to be enabled after enabling '
        'success status button then enabling fail status button')

    toolbar.fail_status_button.disable()

    assert toolbar.fail_status_button.is_disabled(), (
        'Expected fail status button to be disabled after enabling '
        'success status button then disabling fail status button')

    assert toolbar.success_status_button.is_enabled(), (
        'Expected success status button to be enabled after enabling '
        'success status button then disabling fail status button')

    toolbar.success_status_button.disable()

    assert toolbar.fail_status_button.is_enabled(), (
        'Expected fail status button to be enabled after disabling '
        'fail status button then disabling success status button')

    assert toolbar.success_status_button.is_disabled(), (
        'Expected success status button to be disabled after disabling '
        'fail status button then disabling success status button')

    toolbar.fail_status_button.disable()

    assert toolbar.success_status_button.is_enabled(), (
        'Expected success status button to be enabled after disabling '
        'success status button then disabling fail status button')

    assert toolbar.fail_status_button.is_disabled(), (
        'Expected fail status button to be disabled after disabling '
        'success status button then disabling fail status button')

    toolbar.fail_status_button.enable()

    assert toolbar.success_status_button.is_enabled(), (
        'Expected success status button to be enabled after enabling '
        'success status button then disabling and re-enabling fail '
        'status button')

    assert toolbar.fail_status_button.is_enabled(), (
        'Expected fail status button to be enabled after enabling '
        'success status button then disabling and re-enabling fail '
        'status button')
