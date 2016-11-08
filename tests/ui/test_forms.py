import itertools

import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'module_install_enterprise_license',
    )
]


def check_form_required_fields(form):
    """Verify save enabled / disabled behavior for required input fields
    """
    msg_fail_enabled = 'save enabled after clearing required field: '
    msg_fail_disabled = 'save disabled after populating required field: '

    [f.randomize() for f in form.required_fields if not f.value]
    assert form.save.is_enabled(), msg_fail_disabled + '(all)'

    for name, field in itertools.izip(form.required, form.required_fields):
        if field.options:
            continue
        initial_value = field.value
        field.clear()
        assert not form.save.is_enabled(), msg_fail_enabled + name
        field.value = initial_value
        assert form.save.is_enabled(), msg_fail_disabled + name


CREDENTIAL_TYPES = [
    'machine',
    'openstack',
    'aws',
    'gce',
    'azure_classic',
    'azure_resource_manager',
    'rackspace',
    'vmware_vcenter',
    'source_control',
    'satellite_v6',
    'cloudforms',
    'network',
]


@pytest.mark.parametrize('credential_type', CREDENTIAL_TYPES)
def test_credential_form_required_fields(max_window, ui_credential_edit, credential_type):
    credential_form = getattr(ui_credential_edit.details, credential_type)
    check_form_required_fields(credential_form)


def test_inventory_form_required_fields(max_window, ui_inventory_edit):
    check_form_required_fields(ui_inventory_edit.details)


def test_job_template_form_required_fields(max_window, ui_job_template_edit):
    check_form_required_fields(ui_job_template_edit.details)


def test_organization_form_required_fields(max_window, ui_organization_edit):
    check_form_required_fields(ui_organization_edit.details)


def test_project_form_required_fields(max_window, ui_project_edit):
    check_form_required_fields(ui_project_edit.details)


def test_team_form_required_fields(max_window, ui_team_edit):
    check_form_required_fields(ui_team_edit.details)


def test_user_form_required_fields(max_window, ui_user_edit):
    check_form_required_fields(ui_user_edit.details)
