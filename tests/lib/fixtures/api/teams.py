import pytest
import common.utils


@pytest.fixture(scope="function")
def team(request, authtoken, organization):
    payload = dict(name="team_%s" % common.utils.random_unicode(),
                   description="Random Team (%s)" % common.utils.random_unicode(),
                   organization=organization.id,)
    obj = organization.get_related('teams').post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def many_teams(request, authtoken, many_organizations):

    obj_list = list()
    for i, organization in enumerate(many_organizations):
        payload = dict(name="%s many teams" % common.utils.random_unicode(),
                       description="Some Random Team (%s)" % common.utils.random_unicode(),
                       organization=organization.id,)
        obj = organization.get_related('teams').post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list
