import pytest
import fauxfactory
import towerkit.exceptions


@pytest.fixture(scope="function")
def team(request, authtoken, organization):
    payload = dict(name="team_%s" % fauxfactory.gen_utf8(),
                   description="Random Team (%s)" % fauxfactory.gen_utf8(),
                   organization=organization.id,)
    obj = organization.get_related('teams').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def team_with_org_admin(request, team, org_admin):
    '''A team with an org_admin as a member'''
    users_pg = team.get_related('users')
    payload = dict(id=org_admin.id)
    with pytest.raises(towerkit.exceptions.NoContent):
        users_pg.post(payload)
    return team
