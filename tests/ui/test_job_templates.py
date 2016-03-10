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


@pytest.fixture(params=('ui_job_templates_add', 'ui_job_templates_edit'))
def ui_job_templates_update(request):
    return request.getfuncargvalue(request.param)


@pytest.mark.usefixtures('supported_window_sizes')
def test_details_component_visibility(ui_job_templates_update):
    """Verify basic details form component visibility
    """
    assert ui_job_templates_update.details.machine_credential.is_displayed(), (
        'Machine credential form element unexpectedly not displayed')


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_add_job_template(ui_job_templates):
    """Basic end-to-end verification for creating a job template
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_delete_job_template(job_template, ui_job_templates):
    """Basic end-to-end verification for deleting a job template
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_update_job_template(ui_job_templates_edit):
    """Basic end-to-end verification for updating a job template
    """
    pass  # TODO: implement
