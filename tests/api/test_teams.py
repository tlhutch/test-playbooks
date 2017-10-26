"""# 1) Verify teams with unicode names
# 2) Verify credentials, owned by the team, are removed upon DELETE
"""

from towerkit.config import config
import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def some_team(request, authtoken, organization):
    payload = dict(name="some_team: %s" % fauxfactory.gen_utf8(),
                   organization=organization.id)
    obj = organization.get_related('teams').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def some_team_credential(request, authtoken, some_team):
    """Create ssh credential"""
    payload = dict(name="credential-%s" % fauxfactory.gen_utf8(),
                   description="machine credential for team:%s" % some_team.name,
                   kind='ssh',
                   team=some_team.id,
                   username=config.credentials['ssh']['username'],
                   password=config.credentials['ssh']['password'],)
    obj = some_team.get_related('credentials').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


def team_payload(**kwargs):
    payload = kwargs
    if 'name' not in kwargs:
        payload['name'] = fauxfactory.gen_utf8()
    if 'description' not in kwargs:
        payload['description'] = fauxfactory.gen_utf8()
    return payload


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Teams(Base_Api_Test):
    """Tests related to the /api/v1/teams endpoint."""

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

    def test_duplicate(self, api_teams_pg, some_team):
        """Verify that teamnames are unique"""
        payload = dict(name=some_team.name,
                       organization=some_team.organization)
        with pytest.raises(towerkit.exceptions.Duplicate):
            api_teams_pg.post(payload)

    def test_privileged_user_can_create_team(self, request, api_teams_pg, privileged_user, user_password, organization):
        """Verify that a privileged user can create teams."""
        with self.current_user(privileged_user.username, user_password):
            obj = api_teams_pg.post(team_payload(organization=organization.id))
            request.addfinalizer(obj.delete)

    def test_unprivileged_user_cannot_create_team(self, api_teams_pg, unprivileged_user, user_password, organization):
        """Verify that a normal unprivileged user cannot create teams."""
        with self.current_user(unprivileged_user.username, user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                api_teams_pg.post(team_payload(organization=organization.id))

    def test_non_superuser_cannot_create_team_in_another_organization(self, api_teams_pg, non_superuser, user_password, organization,
                                                                      install_enterprise_license_unlimited, another_organization):
        """Verify that only an organization admin can only create teams within
        their organization.
        """
        with self.current_user(non_superuser.username, user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                api_teams_pg.post(team_payload(organization=another_organization.id))

    def test_organization_cascade_delete(self, team):
        """Verifies that teams get cascade deleted along with their organization."""
        team.get_related("organization").delete()
        with pytest.raises(towerkit.exceptions.NotFound):
            team.get()
