import pytest
import fauxfactory


@pytest.fixture(scope="function")
def team(organization, factories):
    team = factories.team(name="team_%s" % fauxfactory.gen_utf8(),
                          description="Random Team (%s)" % fauxfactory.gen_utf8(),
                          organization=organization)
    return team


@pytest.fixture(scope="function")
def team_with_org_admin(team, org_admin):
    """A team with an org_admin as a member"""
    team.set_object_roles(org_admin, "member")
    return team
