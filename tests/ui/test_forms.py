import fauxfactory
import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'module_install_enterprise_license',
    )
]


# -----------------------------------------------------------------------------
# Assertion Helpers and Utilities
# -----------------------------------------------------------------------------


def check_form_responsiveness(form):
    for name, field in form.get_regions():
        # check component visbility
        assert field.is_displayed(), (
            '{0} field group unexpectedly not displayed'.format(name))
        assert field.label.is_displayed(), (
            '{0} field label unexpectedly not displayed'.format(name))
    # pipe some long string data to any form widget group with a text field
    for field_type in ('text_input', 'password', 'text_area', 'email', 'lookup'):
        for name, field in form.get_regions(region_type=field_type):
            if field_type == 'lookup':
                field.set_value(fauxfactory.gen_utf8(length=120), retry=False)
            else:
                field.set_value(fauxfactory.gen_utf8(length=120))
    # verify form groups aren't extended breaking panel boundaries
    for name, field in form.get_regions():
        assert form.surrounds(field), (
            '{0} field group not fully surrounded by panel'.format(name))


def check_form_required_fields(form):
    """Verify form behavior for required input fields
    """
    # Add data to any empty required fields
    for field_type in ['text_input', 'password', 'text_area', 'lookup', 'email']:
        for name, field in form.get_regions(region_type=field_type, required=True):
            if not field.get_value():
                if field_type == 'email':
                    field.set_value(fauxfactory.gen_email())
                else:
                    field.set_value(fauxfactory.gen_alphanumeric())
    for field_type in ['text_input', 'password', 'text_area', 'lookup', 'email']:
        for name, field in form.get_regions(region_type=field_type, required=True):
            assert form.save.is_enabled(), (
                'Form save button unexpectedly not clickable')
            # get current text field value
            initial_value = field.get_value()
            # clear the text
            field.clear()
            # verify the form is not capable of submission
            assert not form.save.is_enabled(), (
                'Form save button unexpectedly clickable after clearing'
                ' required {0} field'.format(name))
            # put the text back
            field.set_value(initial_value)
            assert form.save.is_enabled(), (
                'Form save button unexpectedly not clickable after'
                ' repopulating {0} field'.format(name))


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_job_template_form_required_fields(max_window, ui_job_template_edit):
    check_form_required_fields(ui_job_template_edit.details)


def test_user_form_required_fields(max_window, ui_user_edit):
    check_form_required_fields(ui_user_edit.details)


def test_inventory_form_required_fields(max_window, ui_inventory_edit):
    check_form_required_fields(ui_inventory_edit.details)


def test_project_form_required_fields(max_window, ui_project_edit):
    check_form_required_fields(ui_project_edit.details)


def test_team_form_required_fields(max_window, ui_team_edit):
    check_form_required_fields(ui_team_edit.details)


def test_credential_form_required_fields(max_window, ui_credential_edit):
    for credential_form in ui_credential_edit.forms:
        check_form_required_fields(credential_form)


def test_organization_form_required_fields(max_window, ui_organization_edit):
    check_form_required_fields(ui_organization_edit.details)


def test_job_template_form_responsiveness(
        supported_window_sizes, ui_job_template_edit):
    check_form_responsiveness(ui_job_template_edit.details)


def test_user_form_responsiveness(supported_window_sizes, ui_user_edit):
    check_form_responsiveness(ui_user_edit.details)


def test_inventory_form_responsiveness(
        supported_window_sizes, ui_inventory_edit):
    check_form_responsiveness(ui_inventory_edit.details)


def test_project_form_responsiveness(supported_window_sizes, ui_project_edit):
    check_form_responsiveness(ui_project_edit.details)


def test_team_form_responsiveness(supported_window_sizes, ui_team_edit):
    check_form_responsiveness(ui_team_edit.details)


def test_credential_form_responsiveness(
        supported_window_sizes, ui_credential_edit):
    for credential_form in ui_credential_edit.forms:
        check_form_responsiveness(credential_form)


def test_organization_form_responsiveness(max_window, ui_organization_edit):
    check_form_responsiveness(ui_organization_edit.details)
