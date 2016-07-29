import fauxfactory
import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
    )
]


# -----------------------------------------------------------------------------
# Assertion Helpers and Utilities
# -----------------------------------------------------------------------------

def check_form_responsiveness(form):
    """Verify basic form component visibility and responsiveness
    """
    # pipe some long string data to any form widget group with a text field
    for field_type in ['text_input', 'password', 'text_area', 'email']:
        for name, field in form.get_regions(region_type=field_type):
            field.set_value(fauxfactory.gen_alphanumeric(length=120))
    # https://github.com/ansible/ansible-tower/issues/1461
    for name, field in form.get_regions(region_type='lookup'):
        field.set_value(fauxfactory.gen_alphanumeric(length=120), retry=False)
    # verify form groups aren't extended breaking panel boundaries
    for name, field in form.get_regions():
        assert form.surrounds(field), (
            '{0} field group not fully surrounded by panel'.format(name))


def check_form_required_fields(form):
    """Verify form behavior for required input fields
    """
    data_generators = [
        ('password', fauxfactory.gen_alphanumeric),
        ('text_input', fauxfactory.gen_alphanumeric),
        ('text_area', fauxfactory.gen_alphanumeric),
        ('email', fauxfactory.gen_email),
        ('lookup', fauxfactory.gen_alphanumeric)
    ]
    for field_type, data_generator in data_generators:
        for name, field in form.get_regions(region_type=field_type, required=True):
            if not field.get_value():
                field.set_value(data_generator())
    for field_type, _ in data_generators:
        for name, field in form.get_regions(region_type=field_type, required=True):
            assert form.save.is_enabled(), 'Form save button unexpectedly disabled'
            # get current text field value
            initial_value = field.get_value()
            # clear the text
            field.clear()
            # verify the form is not capable of submission
            assert not form.save.is_enabled(), (
                'save button unexpectedly enabled after clearing'
                ' required {0} field'.format(name))
            # put the text back
            field.set_value(initial_value)
            assert form.save.is_enabled(), (
                'save button unexpectedly disabled after'
                ' repopulating required {0} field'.format(name))


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

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


def test_credential_form_responsiveness(max_window, ui_credential_edit):
    check_form_responsiveness(ui_credential_edit.details.aws)


def test_inventory_form_required_fields(max_window, ui_inventory_edit):
    check_form_required_fields(ui_inventory_edit.details)


def test_inventory_form_responsiveness(supported_window_sizes, ui_inventory_edit):
    check_form_responsiveness(ui_inventory_edit.details)


def test_job_template_form_required_fields(max_window, ui_job_template_edit):
    check_form_required_fields(ui_job_template_edit.details)


def test_job_template_form_responsiveness(supported_window_sizes, ui_job_template_edit):
    check_form_responsiveness(ui_job_template_edit.details)


def test_organization_form_required_fields(max_window, ui_organization_edit):
    check_form_required_fields(ui_organization_edit.details)


def test_organization_form_responsiveness(supported_window_sizes, ui_organization_edit):
    check_form_responsiveness(ui_organization_edit.details)


def test_project_form_required_fields(max_window, ui_project_edit):
    check_form_required_fields(ui_project_edit.details)


def test_project_form_responsiveness(supported_window_sizes, ui_project_edit):
    check_form_responsiveness(ui_project_edit.details)


def test_team_form_required_fields(max_window, ui_team_edit):
    check_form_required_fields(ui_team_edit.details)


def test_team_form_responsiveness(supported_window_sizes, ui_team_edit):
    check_form_responsiveness(ui_team_edit.details)


def test_user_form_required_fields(max_window, ui_user_edit):
    check_form_required_fields(ui_user_edit.details)


def test_user_form_responsiveness(supported_window_sizes, ui_user_edit):
    check_form_responsiveness(ui_user_edit.details)
