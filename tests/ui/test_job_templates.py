import time

import fauxfactory
import pytest
from selenium.common.exceptions import TimeoutException

from towerkit.exceptions import NotFound


def test_machine_credential_association(v1, ui, job_template, session_machine_credential):
    """Verify machine credential association using an existing job template
    """
    edit = ui.job_template_edit.get(id=job_template.id)
    edit.details.credential.value = session_machine_credential.name
    edit.details.save.click()
    assert job_template.get().credential == session_machine_credential.id


def test_cloud_credential_association(v1, ui, job_template, session_cloud_credential):
    """Verify machine credential association using an existing job template
    """
    edit = ui.job_template_edit.get(id=job_template.id)
    edit.details.cloud_credential.value = session_cloud_credential.name
    time.sleep(5)
    edit.details.save.click()
    assert job_template.get().cloud_credential == session_cloud_credential.id


def test_network_credential_association(v1, ui, job_template, session_network_credential):
    """Verify machine credential association using an existing job template"""
    edit = ui.job_template_edit.get(id=job_template.id)
    edit.details.network_credential.value = session_network_credential.name
    time.sleep(5)
    edit.details.save.click()
    assert job_template.get().network_credential == session_network_credential.id


def test_job_template_verbosity_selection(ui, job_template):
    """Verify that the loaded verbosity setting is correct"""
    edit = ui.job_template_edit.get(id=job_template.id)
    assert str(job_template.verbosity) in edit.details.verbosity.value


def test_edit_job_template(v1, ui, job_template):
    """End-to-end functional test for updating an existing job template
    """
    edit = ui.job_template_edit.get(id=job_template.id)
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    job_tags = fauxfactory.gen_alphanumeric()
    # update the job template
    edit.details.description.value = description
    edit.details.job_tags.value = job_tags
    edit.details.name.value = name
    edit.details.save.click()
    edit.table.wait_for_table_to_load()
    # get job_template data api side
    job_template.get()
    # verify the update took place
    assert job_template.name == name, (
        'Unable to verify successful update of job_template')
    assert job_template.description == description, (
        'Unable to verify successful update of job_template')
    assert job_template.job_tags == job_tags, (
        'Unable to verify successful update of job_template')
    # query the table for the edited job_template
    edit.search(name)
    results = edit.table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated job_template name
    assert len(results) == 1, 'Unable to find row of updated job template'


def test_delete_job_template(v1, ui, job_template):
    """End-to-end functional test for deleting a job template
    """
    ui_job_templates = ui.job_templates.get()
    # add a search filter for the job template
    ui_job_templates.search(job_template.name)
    # query the list for the newly created job template
    results = ui_job_templates.table.query(lambda r: r.name.text == job_template.name)
    # delete the job template
    with ui_job_templates.handle_dialog(lambda d: d.action.click()):
        results.pop().delete.click()
    ui_job_templates.table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound):
        job_template.get()
    # verify that the deleted resource is no longer displayed
    ui_job_templates.search.clear()
    ui_job_templates.search(job_template.name)
    assert len(ui_job_templates.table.rows) == 0


def test_create_job_template(v1, ui, session_inventory,
                             session_machine_credential, session_project):
    """End-to-end functional test for creating a job template
    """
    add = ui.job_template_add.get()
    add.table.wait_for_table_to_load()
    add.wait.until(lambda _: 'Run' in add.details.job_type.options)
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    add.details.project.value = session_project.name
    add.details.credential.value = session_machine_credential.name
    add.details.inventory.value = session_inventory.name
    add.details.job_type.value = 'Run'
    add.details.playbook.value = 'ping.yml'
    add.details.verbosity.value = '0 (Normal)'
    add.details.name.value = name
    # save the job template
    add.details.scroll_save_into_view().click()
    add.table.wait_for_table_to_load()
    # verify the update took place api-side
    try:
        add.wait.until(lambda _: v1.job_templates.get(name=name).results)
    except TimeoutException:
        pytest.fail('unable to verify creation of job template')
    # check that we find a row showing the updated job_template name
    add.get().search(name)
    results = add.table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of job template'
