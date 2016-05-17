import fauxfactory
import pytest

from common.utils import random_utf8

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_basic_license',
        'maximized_window_size'
    )
]


@pytest.fixture(params=[
    'ui_job_templates_edit',
    'ui_users_edit',
    'ui_inventories_edit',
    'ui_inventory_scripts_edit',
    'ui_organizations_edit',
    'ui_projects_edit',
    'ui_teams_edit',
    'ui_credentials_edit',
])
def form_page(request):
    return request.getfuncargvalue(request.param)


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1907')
@pytest.mark.usefixtures('supported_window_sizes')
def test_details_component_visibility(form_page):
    """Verify basic form component visibility and responsiveness
    """
    for form in form_page.forms:
        for name, field in form.get_regions():
            # check component visbility
            assert field.is_displayed(), (
                '{0} field group unexpectedly not displayed'.format(name))
            assert field.label.is_displayed(), (
                '{0} field label unexpectedly not displayed'.format(name))

        # pipe some long string data to any form widget group with a text field
        for name, field in form.get_regions(region_type='lookup'):
            field.set_text(random_utf8(length=120), retry=False)

        for field_type in ('text_input', 'password', 'text_area', 'email'):
            for name, field in form.get_regions(region_type=field_type):
                field.set_text(random_utf8(length=120))

        # verify form groups aren't extended breaking panel boundaries
        for name, field in form.get_regions():
            assert form.surrounds(field), (
                '{0} field group not fully surrounded by panel'.format(name))


def test_required_fields(form_page):
    """Verify form behavior for required input fields
    """
    for form in form_page.forms:
        # Add data to any empty required fields
        for field_type in ('text_input', 'password', 'text_area', 'lookup', 'email'):
            for name, field in form.get_regions(region_type=field_type, required=True):
                if not field.text:
                    if field_type == 'email':
                        field.set_text(fauxfactory.gen_email())
                    else:
                        field.set_text(fauxfactory.gen_alphanumeric())

        for field_type in ('text_input', 'password', 'text_area', 'lookup', 'email'):
            for name, field in form.get_regions(region_type=field_type, required=True):
                assert form.save.is_clickable(), (
                    'Form save button unexpectedly not clickable')
                # get current text field value
                text_initial = field.value
                # clear the text
                field.clear()
                # verify the form is not capable of submission
                assert not form.save.is_clickable(), (
                    'Form save button unexpectedly clickable after clearing'
                    ' required {0} field'.format(name))
                # put the text back
                field.set_text(text_initial)
                assert form.save.is_clickable(), (
                    'Form save button unexpectedly not clickable after'
                    ' repopulating {0} field'.format(name))
