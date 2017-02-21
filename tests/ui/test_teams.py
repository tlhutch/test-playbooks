import time

import fauxfactory
import pytest

from towerkit.exceptions import NotFound


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='module')
def team(v1, session_org):
    obj = v1.teams.create(organization=session_org)
    yield obj
    obj.silent_cleanup()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4174')
def test_edit_team(ui, team):
    """Basic end-to-end functional test for updating an existing team"""
    edit = ui.team_edit.get(id=team.id)
    # make some data
    name = fauxfactory.gen_alphanumeric()
    description = fauxfactory.gen_alphanumeric()
    # update the team
    edit.details.name.value = name
    edit.details.description.value = description
    # save the team
    edit.details.save.click()
    edit.table.wait_for_table_to_load()
    # get team data api-side
    team.get()
    # verify the update took place
    assert team.name == name, (
        'Unable to verify successful update of team')
    assert team.description == description, (
        'Unable to verify successful update of team')
    # query the table for the edited team
    edit.search(team.name)
    results = edit.table.query(lambda r: r.name.text == name)
    # check that we find a row showing the updated team name
    assert len(results) == 1, 'Unable to find row of updated team'


def test_delete_team(ui, team):
    """End-to-end functional test for deleting a team"""
    ui_teams = ui.teams.get()
    # add a search filter for the team
    ui_teams.search(team.name)
    # query the list for the newly created team
    results = ui_teams.table.query(lambda r: r.name.text == team.name)
    # delete the team
    with ui_teams.handle_dialog(lambda d: d.action.click()):
        results.pop().delete.click()
    ui_teams.table.wait_for_table_to_load()
    # verify deletion api-side
    with pytest.raises(NotFound):
        team.get()
    # verify that the deleted resource is no longer displayed
    ui_teams.search.clear()
    ui_teams.search(team.name)
    results = ui_teams.table.query(lambda r: r.name.text == team.name)
    assert len(results) == 0


def test_create_team(v1, ui, session_org):
    """End-to-end functional test for creating a team"""
    add = ui.team_add.get()
    # make some data
    name = fauxfactory.gen_alphanumeric()
    # populate the form
    add.details.name.value = name
    add.details.organization.value = session_org.name
    # save the team
    time.sleep(5)
    add.details.save.click()
    add.table.wait_for_table_to_load()
    # verify the update took place api-side
    add.passively_wait_until(lambda: v1.teams.get(name=name).results)
    api_results = v1.teams.get(name=name).results
    assert len(api_results) == 1, 'unable to verify creation of team'
    # check that we find a row showing the updated name
    add.search(name)
    ui_results = add.table.query(lambda r: r.name.text == name)
    assert len(ui_results) == 1, 'unable to verify creation of team'
