import time

import fauxfactory
import pytest
from selenium.common.exceptions import TimeoutException

from qe.exceptions import NotFound_Exception
from qe.ui.models import JobTemplateEdit

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
    editPage = JobTemplateEdit(selenium, base_url, id=template.id).open()

    machine_credential = factories.credential(kind='ssh')

    editPage.details.credential.set_value(machine_credential.name)
    editPage.details.save.click()

    assert template.get().credential == machine_credential.id


def test_cloud_credential_association(factories, ui_dashboard, selenium, base_url):
    """Verify cloud credential association using an existing job template"""
    template = factories.job_template()
    editPage = JobTemplateEdit(selenium, base_url, id=template.id).open()

    cloud_credential = factories.credential(kind='aws', username='foo', password='bar')

    editPage.details.cloud_credential.set_value(cloud_credential.name)
    editPage.details.save.click()

    assert template.get().cloud_credential == cloud_credential.id


def test_network_credential_association(factories, ui_dashboard, selenium, base_url):
    """Verify network credential association using an existing job template"""
    template = factories.job_template()
    editPage = JobTemplateEdit(selenium, base_url, id=template.id).open()

    network_credential = factories.credential(kind='net')

    editPage.details.network_credential.set_value(network_credential.name)
    editPage.details.save.click()

    assert template.get().network_credential == network_credential.id


def test_job_template_verbosity_selection(factories, ui_dashboard, selenium, base_url):
    """Verify that the loaded verbosity setting is correct"""
    template = factories.job_template(verbosity=2)
    editPage = JobTemplateEdit(selenium, base_url, id=template.id).open()
    assert str(template.verbosity) in editPage.details.verbosity.get_value()


def test_edit_job_template(api_job_templates_pg, ui_job_template_edit):
    """Basic end-to-end functional test for updating an existing job template
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    job_tags = fauxfactory.gen_alphanumeric()
    # update the job template
    ui_job_template_edit.details.name.set_value(name)
    ui_job_template_edit.details.description.set_value(description)
    ui_job_template_edit.details.job_tags.set_value(job_tags)
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
    results = ui_job_templates.list_table.query(
        lambda r: r.name.text == job_template.name)
    # delete the job template
    results.pop().delete.click()
    # confirm deletion
    ui_job_templates.dialog.confirm.click()
    ui_job_templates.list_table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound_Exception):
        job_template.get()
    # verify that the deleted resource is no longer displayed
    results = ui_job_templates.list_table.query(
        lambda r: r.name.text == job_template.name)
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
    ui_job_template_add.details.project.set_value(project.name)
    ui_job_template_add.details.credential.set_value(credential.name)
    ui_job_template_add.details.inventory.set_value(inventory.name)
    ui_job_template_add.details.job_type.set_value('Run')
    ui_job_template_add.details.playbook.set_value('ping.yml')
    ui_job_template_add.details.verbosity.set_value('0 (Normal)')
    ui_job_template_add.details.name.set_value(name)
    # save the job template
    time.sleep(5)
    ui_job_template_add.details.scroll_save_into_view().click()
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
