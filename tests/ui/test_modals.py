import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'install_enterprise_license_unlimited',
        'maximized_window_size'
    )
]


def check_modal_blur_click(modal):
    """Check that the modal window does not disappear when the user clicks
    clicks out of focus
    """
    from selenium.common.exceptions import TimeoutException

    assert modal.is_displayed(), 'modal unexpectedly not displayed'

    modal.click_outside()

    with pytest.raises(TimeoutException):
        modal.wait_until_not_displayed()


@pytest.mark.usefixtures('inventory')
def test_inventory_delete_modal_blur_click(ui_inventories):
    """Check that the delete modal window does not disappear when the user
    clicks out of focus
    """
    prompt_modal = ui_inventories.table[0]['delete'].click()
    check_modal_blur_click(prompt_modal)


@pytest.mark.usefixtures('project')
def test_projects_delete_modal_blur_click(ui_projects):
    """Check that the delete modal window does not disappear when the user
    clicks out of focus
    """
    prompt_modal = ui_projects.table[0]['delete'].click()
    check_modal_blur_click(prompt_modal)


@pytest.mark.usefixtures('job_template')
def test_job_templates_delete_modal_blur_click(ui_job_templates):
    """Check that the delete modal window does not disappear when the user
    clicks out of focus
    """
    prompt_modal = ui_job_templates.table[0]['delete'].click()
    check_modal_blur_click(prompt_modal)


@pytest.mark.skipif(True, reason='Requires a job_with_schedule fixture')
@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
    'job_with_schedule',
)
def test_jobs_delete_modal_blur_click(ui_jobs):
    """Check that the delete modal window does not disappear when the user
    clicks out of focus
    """
    prompt_modal = ui_jobs.jobs.table[0]['delete'].click()
    check_modal_blur_click(prompt_modal)
    ui_jobs.refresh()

    prompt_modal = ui_jobs.schedules.table[0]['delete'].click()
    check_modal_blur_click(prompt_modal)


@pytest.mark.usefixtures('anonymous_user')
def test_users_delete_modal_blur_click(ui_users):
    """Check that the delete modal window does not disappear when the user
    clicks out of focus
    """
    prompt_modal = ui_users.table[0]['delete'].click()
    check_modal_blur_click(prompt_modal)


@pytest.mark.usefixtures('team')
def test_teams_delete_modal_blur_click(ui_teams):
    """Check that the delete modal window does not disappear when the user
    clicks out of focus
    """
    prompt_modal = ui_teams.table[0]['delete'].click()
    check_modal_blur_click(prompt_modal)
