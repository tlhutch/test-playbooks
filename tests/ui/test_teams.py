import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures('maximized_window_size')
]


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_create_team(api_teams_pg, ui_teams_add):
    """Basic end-to-end verification for creating a team
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_update_team(api_teams_pg, ui_teams_edit):
    """Basic end-to-end verification for updating a team
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_delete_team(team, api_teams_pg, ui_teams):
    """Basic end-to-end verification for deleting a team
    """
    pass  # TODO: implement
