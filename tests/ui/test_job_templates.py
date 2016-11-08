import time

import fauxfactory
import pytest
from selenium.common.exceptions import TimeoutException

from towerkit.exceptions import NotFound
from towerkit.ui.models import JobTemplateEdit

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
        'max_window',
    )
]


def test_machine_credential_association(factories, ui_dashboard, selenium, base_url):
    """Verify machine credential association using an existing job template"""
    template = factories.job_template()
    cred = factories.credential(kind='ssh')

    edit = JobTemplateEdit(selenium, base_url, id=template.id).open()
    edit.details.credential.value = cred.name

    time.sleep(5)
    edit.details.save.click()

    assert template.get().credential == cred.id


def test_cloud_credential_association(factories, ui_dashboard, selenium, base_url):
    """Verify cloud credential association using an existing job template"""
    template = factories.job_template()
    cred = factories.credential(kind='aws', username='foo', password='bar')

    edit = JobTemplateEdit(selenium, base_url, id=template.id).open()
    edit.details.cloud_credential.value = cred.name

    time.sleep(5)
    edit.details.save.click()

    assert template.get().cloud_credential == cred.id


def test_network_credential_association(factories, ui_dashboard, selenium, base_url):
    """Verify network credential association using an existing job template"""
    template = factories.job_template()
    cred = factories.credential(kind='net')

    edit = JobTemplateEdit(selenium, base_url, id=template.id).open()
    edit.details.network_credential.value = cred.name

    time.sleep(5)
    edit.details.save.click()

    assert template.get().network_credential == cred.id


def test_job_template_verbosity_selection(factories, ui_dashboard, selenium, base_url):
    """Verify that the loaded verbosity setting is correct"""
    template = factories.job_template(verbosity=2)
    edit = JobTemplateEdit(selenium, base_url, id=template.id).open()
    assert str(template.verbosity) in edit.details.verbosity.value


def test_edit_job_template(api_job_templates_pg, ui_job_template_edit):
    """Basic end-to-end functional test for updating an existing job template
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    job_tags = fauxfactory.gen_alphanumeric()
    # update the job template
    ui_job_template_edit.details.name.value = name
    ui_job_template_edit.details.description.value = description
    ui_job_template_edit.details.job_tags.value = job_tags
    # save the job template
    time.sleep(5)
    ui_job_template_edit.details.save.click()
    ui_job_template_edit.list_table.wait_for_table_to_load()
    # get job_template data api side
    api_job_template = api_job_templates_pg.get(
        id=ui_job_template_edit.kwargs['id']).results[0]
    # verify the update took place
    assert api_job_template.name == name, (
        'Unable to verify successful update of job_template')
    assert api_job_template.description == description, (
        'Unable to verify successful update of job_template')
    assert api_job_template.job_tags == job_tags, (
        'Unable to verify successful update of job_template')
    # query the table for the edited job_template
    results = ui_job_template_edit.list_table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated job_template name
    assert len(results) == 1, 'Unable to find row of updated job template'


def test_delete_job_template(factories, ui_job_templates):
    """Basic end-to-end verification for deleting a job template
    """
    job_template = factories.job_template()
    # add a search filter for the job template
    ui_job_templates.driver.refresh()
    ui_job_templates.list_table.wait_for_table_to_load()
    ui_job_templates.list_search.add_filter('name', job_template.name)
    # query the list for the newly created job template
    results = ui_job_templates.list_table.query(lambda r: r.name.text == job_template.name)
    # delete the job template
    results.pop().delete.click()
    # confirm deletion
    ui_job_templates.dialog.action.click()
    ui_job_templates.list_table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound):
        job_template.get()
    # verify that the deleted resource is no longer displayed
    results = ui_job_templates.list_table.query(lambda r: r.name.text == job_template.name)
    assert not results


def test_create_job_template(factories, api_job_templates_pg, ui_job_template_add):
    """Basic end-to-end verification for creating a job template
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    organization = factories.organization()
    project = factories.project(organization=organization)
    credential = factories.credential(organization=organization)
    inventory = factories.inventory(organization=organization)
    # populate the form
    ui_job_template_add.driver.refresh()
    ui_job_template_add.list_table.wait_for_table_to_load()

    details = ui_job_template_add.details
    details.name.value = name
    details.project.value = project.name
    details.credential.value = credential.name
    details.inventory.value = inventory.name
    time.sleep(5)
    details.job_type.value = 'Run'
    details.playbook.value = 'ping.yml'
    details.verbosity.value = '0 (Normal)'
    # save the job template
    time.sleep(5)
    details.scroll_save_into_view()
    details.save.click()
    ui_job_template_add.list_table.wait_for_table_to_load()
    # verify the update took place api-side
    try:
        ui_job_template_add.wait.until(lambda _: api_job_templates_pg.get(name=name).results)
    except TimeoutException:
        pytest.fail('unable to verify creation of job template')
    # check for expected url content
    api_results = api_job_templates_pg.get(name=name).results
    expected_url_content = '/#/job_templates/{0}'.format(api_results[0].id)
    assert expected_url_content in ui_job_template_add.driver.current_url
    # check that we find a row showing the updated job_template name
    results = ui_job_template_add.list_table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of job template'
    # check that the newly created resource has the row selection indicator
    assert ui_job_template_add.list_table.selected_row.name.text == name
