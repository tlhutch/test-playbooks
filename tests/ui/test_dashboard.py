from collections import defaultdict
import json

import pytest


pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'module_install_enterprise_license',
        'max_window',
    )
]


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope='module')
def recent_jobs(batch_job_template):
    """Generate varied job run data for the dashboard page
    """
    data = defaultdict(list)
    x_vars = map(json.dumps, [{'fail': False}, {'fail': True}])
    for i in xrange(3):
        jt = batch_job_template(playbook='fail_unless.yml')
        for n in xrange(i+1):
            jt.patch(extra_vars=x_vars[n % 2])
            data[jt.name].append(jt.launch())
    data[jt.name][-1].wait_until_completed()
    return data


# -----------------------------------------------------------------------------
# Assertion Helpers and Utilities
# -----------------------------------------------------------------------------

def check_toolbar_dropdown(dropdown):
    for option in dropdown.options:
        dropdown.set_value(option)
        selected = dropdown.get_value()
        assert selected == option, (
            'unexpected value: {1} != {2}'.format(selected, option))


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_recent_job_template_status_icons(recent_jobs, ui_dashboard):
    """Verify that the recent job_templates table displays the expected
    statuses, job ids, and correct number of job runs.
    """
    ui_dashboard.wait.until(lambda _: ui_dashboard.recent_jobs.is_displayed())
    ui_dashboard.wait.until(lambda _: len(ui_dashboard.recent_jobs.rows) == 5)
    for jt_name, jobs in recent_jobs.iteritems():
        results = ui_dashboard.recent_job_templates.query(
            lambda r: r.name.text == jt_name)
        assert len(results) == 1, 'job template not found in table'
        # get displayed tooltip data for each status icon in the row
        icon_data = [icon.tooltip_text for icon in results.pop().status_icons]
        assert len(icon_data) == len(jobs), 'unexpected number of status icons'
        for icon_text, job in zip(icon_data, list(reversed(jobs))):
            assert job.get().status.lower() in icon_text.lower(), (
                'expected status not shown in tooltip')
            assert str(job.id) in icon_text, 'expected id not shown in tooltip'


def test_job_status_toolbar_dropdowns(ui_dashboard):
    """Cycle through each of the toolbar dropdown options and make sure they
    display correctly
    """
    check_toolbar_dropdown(ui_dashboard.job_status_toolbar.period)
    check_toolbar_dropdown(ui_dashboard.job_status_toolbar.job_type)
    check_toolbar_dropdown(ui_dashboard.job_status_toolbar.status)
