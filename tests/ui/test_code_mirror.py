import pytest

pytestmark = [pytest.mark.ui, pytest.mark.nondestructive]


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3333')
def test_host_vars_formatting(ui_host_edit):
    details = ui_host_edit.details
    # check that the default parse type is yaml
    assert details.variables_parse_type.get_value() == 'yaml'
    assert details.variables.is_yaml()
    # fiddle with parse types and check formatting
    details.variables_parse_type.set_value('json')
    assert details.variables_parse_type.get_value() == 'json'
    assert details.variables.is_json()
    details.extra_variables_parse_type.set_value('yaml')
    assert details.variables_parse_type.get_value() == 'yaml'
    assert details.variables.is_yaml()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3333')
@pytest.mark.parametrize('schedule_page_fixture_name', [
    'ui_job_template_schedule_edit',
    'ui_project_schedule_edit'
])
def test_schedule_extra_vars_formatting(request, schedule_page_fixture_name):
    schedule_page = request.getfixturevalue(schedule_page_fixture_name)
    details = schedule_page.details
    # check that the default parse type is yaml
    assert details.extra_variables_parse_type.get_value() == 'yaml'
    assert details.extra_variables.is_yaml()
    # fiddle with parse types and check formatting
    details.extra_variables_parse_type.set_value('json')
    assert details.extra_variables_parse_type.get_value() == 'json'
    assert details.extra_variables.is_json()
    details.extra_variables_parse_type.set_value('yaml')
    assert details.extra_variables_parse_type.get_value() == 'yaml'
    assert details.extra_variables.is_yaml()
