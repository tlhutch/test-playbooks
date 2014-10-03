'''
# 1) Verify teams with unicode names
# 2) Verify credentials, owned by the team, are removed upon DELETE
'''

import pytest
import common.utils
import common.exceptions
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def some_team(request, testsetup, authtoken, organization):
    payload = dict(name="some_team: %s" % common.utils.random_unicode(),
                   organization=organization.id)
    obj = organization.get_related('teams').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def some_team_credential(request, testsetup, authtoken, some_team):
    '''Create ssh credential'''
    payload = dict(name="credential-%s" % common.utils.random_unicode(),
                   description="machine credential for team:%s" % some_team.name,
                   kind='ssh',
                   team=some_team.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)
    obj = some_team.get_related('credentials').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Teams(Base_Api_Test):
    '''
    Verify the /teams endpoint displays the expected information based on the current team
    '''
    pytestmark = pytest.mark.usefixtures('authtoken')

    def test_duplicate(self, api_teams_pg, some_team):
        '''Verify that teamnames are unique'''
        payload = dict(name=some_team.name,
                       organization=some_team.organization)
        with pytest.raises(common.exceptions.Duplicate_Exception):
            api_teams_pg.post(payload)

    def test_cascade_delete(self, api_credentials_pg, some_team, some_team_credential):
        '''Verify that a credentials, owned by a team, are deleted when the team is deleted'''

        # Delete the team
        some_team.delete()

        # Shouldn't be able to query credentials for the deleted team
        with pytest.raises(common.exceptions.Forbidden_Exception):
            some_team.get_related('credentials')

        # Verify that the teams credentials were deleted
        remaining_creds = api_credentials_pg.get(id=some_team_credential.id)
        assert remaining_creds.count == 0, "The team was deleted, however a credential owned by the team (id:%s) remains" % remaining_creds.results[0].id

        # The credential should have been deleted
        with pytest.raises(common.exceptions.NotFound_Exception):
            some_team_credential.get()
