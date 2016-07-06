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


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/901')
def test_jobs_no_data(api_jobs_pg,  ui_jobs):
    """Verify jobs page region visibility and behavior when no jobs or
    associated schedules are loaded into the system
    """
    for result in api_jobs_pg.get().results:
        result.silent_delete()
    ui_jobs.refresh()
    assert ui_jobs.jobs_tab.is_clickable(), (
        'jobs tab unexpectedly not clickable')
    assert not ui_jobs.jobs.table.is_displayed(), (
        'jobs table unexpectedly displayed with no data available')
    assert not ui_jobs.jobs.search.is_displayed(), (
        'jobs search unexpectedly displayed when no data available')
    assert ui_jobs.schedules_tab.is_clickable(), (
        'schedules tab unexpectedly not clickable')
    assert not ui_jobs.schedules.table.is_displayed(), (
        'schedules table unexpectedly displayed with no data available')
    assert not ui_jobs.schedules.search.is_displayed(), (
        'schedules search unexpectedly displayed with no data available')


@pytest.mark.skipif(True, reason='requires launched job with schedule fixture')
def test_jobs(job_template_with_schedule, ui_jobs):
    """Verify jobs page region visibility and behavior when job and associated
    schedule data is available
    """
    job_template_with_schedule.launch().wait_until_completed()
    assert ui_jobs.jobs_tab.is_clickable(), (
        'jobs tab unexpectedly not clickable with data available')
    assert ui_jobs.jobs.table.is_displayed(), (
        'jobs table unexpectedly not displayed with data available')
    assert ui_jobs.jobs.search.is_displayed(), (
        'jobs search unexpectedly not displayed with data available')
    assert ui_jobs.schedules_tab.is_clickable(), (
        'schedules tab unexpectedly not clickable with data available')
    assert ui_jobs.schedules.table.is_displayed(), (
        'schedules table unexpectedly not displayed with data available')
    assert ui_jobs.schedules.search.is_displayed(), (
        'schedules search unexpectedly not displayed with data available')
