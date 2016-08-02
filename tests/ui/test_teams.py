import time

import fauxfactory
import pytest

from common.exceptions import NotFound_Exception

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
        'max_window',
    )
]


def test_edit_team(api_teams_pg, ui_team_edit):
    """Basic end-to-end functional test for updating an existing team
    """
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the team
    ui_team_edit.details.name.set_value(name)
    ui_team_edit.details.description.set_value(description)
    # save the team
    time.sleep(5)
    ui_team_edit.details.save.click()
    ui_team_edit.list_table.wait_for_table_to_load()
    # get team data api-side
    time.sleep(5)
    api_team = api_teams_pg.get(id=ui_team_edit.kwargs['id']).results[0]
    # verify the update took place
    assert api_team.name == name, (
        'Unable to verify successful update of team')
    assert api_team.description == description, (
        'Unable to verify successful update of team')
    # query the table for the edited team
    results = ui_team_edit.list_table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated team name
    assert len(results) == 1, 'Unable to find row of updated team'


def test_delete_team(factories, ui_teams):
    """Basic end-to-end verification for deleting a team
    """
    team = factories.team()
    # add a search filter for the team
    ui_teams.driver.refresh()
    ui_teams.list_table.wait_for_table_to_load()
    ui_teams.list_search.add_filter('name', team.name)
    # query the list for the newly created team
    results = ui_teams.list_table.query(lambda r: r.name.text == team.name)
    # delete the team
    results.pop().delete.click()
    # confirm deletion
    ui_teams.dialog.confirm.click()
    ui_teams.list_table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound_Exception):
        team.get()
    # verify that the deleted resource is no longer displayed
    results = ui_teams.list_table.query(lambda r: r.name.text == team.name)
    assert not results


def test_create_team(factories, api_teams_pg, ui_team_add):
    """Basic end-to-end verification for creating a team
    """
    # make some data
    organization = factories.organization()
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    ui_team_add.driver.refresh()
    ui_team_add.details.name.set_value(name)
    ui_team_add.details.organization.set_value(organization.name)
    # save the team
    time.sleep(5)
    ui_team_add.details.save.click()
    ui_team_add.list_table.wait_for_table_to_load()
    # verify the update took place api-side
    api_results = api_teams_pg.get(name=name).results
    assert api_results, 'unable to verify creation of team'
    # check for expected url content
    expected_url_content = '/#/teams/{0}'.format(api_results[0].id)
    assert expected_url_content in ui_team_add.driver.current_url
    # check that we find a row showing the updated name
    results = ui_team_add.list_table.query(lambda r: r.name.text == name)
    assert len(results) == 1, 'unable to verify creation of user'
    # check that the newly created resource has the row selection indicator
    assert ui_team_add.list_table.selected_row.name.text == name
