import time 

import fauxfactory
import pytest

from common.exceptions import NotFound_Exception

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'module_install_enterprise_license',
        'max_window',
    )
]


def test_active_project_update(factories, ui_projects):
    """Verify that the project update button is active for a scm project
    """
    # create test project
    project = factories.project()
    # add a search filter for the project
    ui_projects.list_search.add_filter('name', project.name)
    # get displayed table data
    results = ui_projects.list_table.query(lambda r: r.name.text == project.name)
    assert len(results) == 1, 'Expected table data not found'
    # check tooltip status message
    tooltip = results[0].scm_update.get_attribute('aw-tool-tip').lower()
    assert 'start' in tooltip, 'Unexpected scm_update tooltip status message'
    # record api project last_updated date
    api_last_updated = project.last_updated
    # record ui project last_updated date
    ui_last_updated = results[0].last_updated.text
    # initiate SCM update
    results[0].scm_update.click()
    # wait for update to finish
    project.get().wait_until_completed()
    # if we detect a refresh button click it and re-query the table
    if ui_projects.is_refresh_button_displayed():
        ui_projects.refresh.click()
    # get displayed table data
    results = ui_projects.list_table.query(lambda r: r.name.text == project.name)
    assert results[0].scm_update.is_enabled(), (
        'Project update button unexpectedly not clickable')
    # check tooltip status message
    tooltip = results[0].scm_update.get_attribute('aw-tool-tip').lower()
    assert 'start' in tooltip, 'Unexpected scm_update tooltip status message'
    # verify api last_updated changed
    assert api_last_updated != project.last_updated, (
        'api project last_update value unexpectedly unchanged')
    # verify ui last_updated changed
    assert ui_last_updated != results[0].last_updated.text, (
        'ui project last_update value unexpectedly unchanged')


def test_edit_project(api_projects_pg, ui_project_edit):
    """Basic end-to-end functional test for updating an existing project
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the project
    ui_project_edit.details.name.set_value(name)
    ui_project_edit.details.description.set_value(description)
    # save the project
    time.sleep(5)
    ui_project_edit.details.save.click()
    ui_project_edit.list_table.wait_for_table_to_load()
    # get project data api-side
    api_project = api_projects_pg.get(
        id=ui_project_edit.kwargs['id']).results[0]
    # verify the update took place
    assert api_project.name == name, (
        'Unable to verify successful update of project')
    assert api_project.description == description, (
        'Unable to verify successful update of project')
    # query the table for the edited project
    results = ui_project_edit.list_table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated project name
    assert len(results) == 1, 'Unable to find row of updated project'


def test_delete_project(factories, ui_projects):
    """Basic end-to-end verification for deleting a project
    """
    project = factories.project()
    # add a search filter for the project
    ui_projects.driver.refresh()
    ui_projects.list_search.add_filter('name', project.name)
    # query the list for the newly created project
    results = ui_projects.list_table.query(
        lambda r: r.name.text == project.name)
    # delete the project
    results.pop().delete.click()
    # confirm deletion
    ui_projects.dialog.confirm.click()
    ui_projects.list_table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound_Exception):
        project.get()
    # verify that the deleted resource is no longer displayed
    results = ui_projects.list_table.query(
        lambda r: r.name.text == project.name)
    assert not results


def test_create_project(factories, api_projects_pg, ui_project_add):
    """Basic end-to-end verification for creating a project
    """
    # make some data
    data, resources = factories.project.payload()
    org = resources['organization']
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    ui_project_add.driver.refresh()
    ui_project_add.details.name.set_value(name)
    ui_project_add.details.scm_type.set_value(data['scm_type'].title())
    ui_project_add.details.scm_url.set_value(data['scm_url'])
    ui_project_add.details.organization.set_value(org.name)
    # save the project
    time.sleep(5)
    ui_project_add.details.save.click()
    ui_project_add.list_table.wait_for_table_to_load()
    # verify the update took place api-side
    api_results = api_projects_pg.get(name=name).results
    assert api_results, 'unable to verificationerify creation of project'
    # wait for newly created project scm_update to finish
    api_project = api_results[0]
    api_project.wait_until_completed()
    # check the current url for the project id
    assert str(api_project.id) in ui_project_add.driver.current_url
    # check that we find a row showing the updated project name
    results = ui_project_add.list_table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of project'
    # check that the row of the newly created resource is the selected row
    assert ui_project_add.list_table.selected_row.name.text == name
    
