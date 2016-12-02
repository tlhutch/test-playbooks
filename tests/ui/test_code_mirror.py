import pytest


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='class')
def manage_host(v1, ui, inventory):
    host = v1.hosts.create(inventory=inventory)
    yield ui.manage_inventory_edit_host.get(id=inventory.id, host_id=host.id)
    host.silent_cleanup()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3333')
def test_host_vars_formatting(manage_host):
    # check that the default parse type is yaml
    details = manage_host.details
    assert details.variables_parse_type.value == 'yaml'
    assert details.variables.is_yaml()
    # fiddle with parse types and check formatting
    details.variables_parse_type.value = 'json'
    assert details.variables_parse_type.value == 'json'
    assert details.variables.is_json()
    details.extra_variables_parse_type.value = 'yaml'
    assert details.variables_parse_type.value == 'yaml'
    assert details.variables.is_yaml()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3882')
def test_schedule_extra_vars_formatting(ui, job_template, job_template_schedule):
    schedule_page = ui.job_template_schedule_edit.get(
        id=job_template.id,
        schedule_id=job_template_schedule.id)
    details = schedule_page.details
    # check that the default parse type is yaml
    assert details.extra_variables_parse_type.value == 'yaml'
    assert details.extra_variables.is_yaml()
    # fiddle with parse types and check formatting
    details.extra_variables_parse_type.value = 'json'
    assert details.extra_variables_parse_type.value == 'json'
    assert details.extra_variables.is_json()
    details.extra_variables_parse_type.value = 'yaml'
    assert details.extra_variables_parse_type.value == 'yaml'
    assert details.extra_variables.is_yaml()
