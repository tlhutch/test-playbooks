import time

import fauxfactory
import pytest

from towerkit.exceptions import NotFound


pytestmark = [pytest.mark.ui]


def test_active_project_update(ui, session_project):
    """Verify that the project update button is active for a scm project
    """
    ui_projects = ui.projects.get()
    # add a search filter for the project
    ui_projects.search(session_project.name)
    # get displayed table data
    results = ui_projects.table.query(lambda r: r.name.text == session_project.name)
    assert len(results) == 1, 'Expected table data not found'
    # check tooltip status message
    tooltip = results[0].scm_update.get_attribute('aw-tool-tip').lower()
    assert 'start' in tooltip, 'Unexpected scm_update tooltip status message'
    # record api project last_updated date
    api_last_updated = session_project.last_updated
    # record ui project last_updated date
    ui_last_updated = results[0].last_updated.text
    # initiate SCM update
    results[0].scm_update.click()
    # wait for update to finish
    session_project.get().wait_until_completed()
    # if we detect a refresh button click it and re-query the table
    if ui_projects.is_refresh_button_displayed():
        ui_projects.refresh.click()
    # get displayed table data
    ui_projects.search.clear()
    ui_projects.search(session_project.name)
    results = ui_projects.table.query(lambda r: r.name.text == session_project.name)
    assert results[0].scm_update.is_enabled(), (
        'Project update button unexpectedly not clickable')
    # check tooltip status message
    tooltip = results[0].scm_update.get_attribute('aw-tool-tip').lower()
    assert 'start' in tooltip, 'Unexpected scm_update tooltip status message'
    # verify api last_updated changed
    assert api_last_updated != session_project.last_updated, (
        'api project last_update value unexpectedly unchanged')
    # verify ui last_updated changed
    assert ui_last_updated != results[0].last_updated.text, (
        'ui project last_update value unexpectedly unchanged')


def test_edit_project(v1, ui, project):
    """End-to-end functional test for updating an existing project
    """
    edit = ui.project_edit.get(id=project.id)
    # these are indicators that the page is actually ready to be used
    edit.table.wait_for_table_to_load()
    edit.wait.until(lambda _: 'Git' in edit.details.scm_type.options)
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the project
    edit.details.name.value = name
    edit.details.description.value = description
    # save the project
    edit.details.save.click()
    edit.table.wait_for_table_to_load()
    # get project data api-side
    project.get()
    # verify the update took place
    assert project.name == name, (
        'Unable to verify successful update of project')
    assert project.description == description, (
        'Unable to verify successful update of project')
    # query the table for the edited project
    edit.search(name)
    results = edit.table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated project name
    assert len(results) == 1, 'Unable to find updated project'


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3816')
def test_delete_project(v1, ui, project):
    """End-to-end functional test for deleting a project
    """
    ui_projects = ui.projects.get()
    # add a search filter for the project
    ui_projects.search(project.name)
    # query the list for the newly created project
    results = ui_projects.table.query(lambda r: r.name.text == project.name)
    # delete the project
    with ui_projects.handle_dialog(lambda d: d.action.click()):
        results.pop().delete.click()
    ui_projects.table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound):
        project.get()
    # verify that the deleted resource is no longer displayed
    ui_projects.search.clear()
    ui_projects.search(project.name)
    results = ui_projects.table.query(lambda r: r.name.text == project.name)
    assert len(results) == 0


def test_create_project(v1, ui, session_org, session_project):
    """End-to-end functional test for creating a project
    """
    add = ui.project_add.get()
    # these are indicators that the page is actually ready to be used
    add.table.wait_for_table_to_load()
    add.wait.until(lambda _: 'Git' in add.details.scm_type.options)
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    add.details.scm_type.value = session_project.scm_type.title()
    add.details.scm_url.value = session_project.scm_url
    add.details.organization.value = session_org.name
    add.details.name.value = name
    # save the project
    time.sleep(5)
    add.find_element('id', 'project_save_btn').click()
    add.table.wait_for_table_to_load()
    # verify the update took place api-side
    add.passively_wait_until(lambda: v1.projects.get(name=name).results)
    api_results = v1.projects.get(name=name).results
    assert api_results, 'unable to verify creation of project'
    # wait for newly created project scm_update to finish
    api_project = api_results[0]
    api_project.get_related('current_update').wait_until_completed()
    # check the current url for the project id
    assert str(api_project.id) in add.driver.current_url
    # check that we find a row showing the updated project name
    add.search(api_project.name)
    results = add.table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of project'
