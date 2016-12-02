from collections import defaultdict
import json

import pytest


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='module')
def create_batch_template(api_v1, session_org):
    """Create a factory for job templates that share the same set of
    resource dependencies
    """
    inv = api_v1.inventory.create(organization=session_org)
    pj = api_v1.projects.create(organization=session_org)
    cred = api_v1.credentials.create(organization=session_org)

    batch_templates = []

    def _create(**kwargs):
        params = {'inventory': inv, 'project': pj, 'credential': cred}
        params.update(kwargs)
        template = api_v1.job_templates.create(**params)
        batch_templates.append(template)
        return template

    yield _create

    for template in batch_templates:
        template.silent_cleanup()

    inv.silent_cleanup()
    pj.silent_cleanup()
    cred.silent_cleanup()


@pytest.fixture(scope='module')
def recent_jobs(create_batch_template):
    """Generate varied job run data for the dashboard page
    """
    data = defaultdict(list)
    x_vars = map(json.dumps, [{'fail': False}, {'fail': True}])
    for i in xrange(3):
        jt = create_batch_template(playbook='fail_unless.yml')
        for n in xrange(i+1):
            jt.patch(extra_vars=x_vars[n % 2])
            data[jt.name].append(jt.launch())
    data[jt.name][-1].wait_until_completed()
    return data


def test_job_status_toolbar_dropdowns(ui):
    """Cycle through each of the toolbar dropdown options and make sure they
    display correctly
    """
    for name in ('period', 'job_type', 'status'):
        dropdown = getattr(ui.dashboard.job_status_toolbar, name)
        for option in dropdown.options:
            dropdown.value = option
            selected = dropdown.value
            assert selected == option, (
                'unexpected value: {1} != {2}'.format(selected, option))


def test_recent_job_template_status_icons(ui, recent_jobs):
    """Verify that the recent job_templates table displays the expected
    statuses, job ids, and correct number of job runs.
    """
    dashboard = ui.dashboard

    dashboard.wait.until(lambda _: dashboard.recent_jobs.is_displayed())
    dashboard.wait.until(lambda _: len(dashboard.recent_jobs.rows) == 5)
    for jt_name, jobs in recent_jobs.iteritems():
        results = dashboard.recent_job_templates.query(lambda r: r.name.text == jt_name)
        assert len(results) == 1, 'job template not found in table'
        # get displayed tooltip data for each status icon in the row
        icon_data = [icon.tooltip_text for icon in results.pop().status_icons]
        assert len(icon_data) == len(jobs), 'unexpected number of status icons'
        for icon_text, job in zip(icon_data, list(reversed(jobs))):
            assert job.get().status.lower() in icon_text.lower(), (
                'expected status not shown in tooltip')
            assert str(job.id) in icon_text, 'expected id not shown in tooltip'
