import pytest
import fauxfactory


@pytest.fixture(scope="function")
def team(request, authtoken, organization):
    payload = dict(name="team_%s" % fauxfactory.gen_utf8(),
                   description="Random Team (%s)" % fauxfactory.gen_utf8(),
                   organization=organization.id,)
    obj = organization.get_related('teams').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def many_teams(request, authtoken, many_organizations):

    obj_list = list()
    for i, organization in enumerate(many_organizations):
        payload = dict(name="%s many teams" % fauxfactory.gen_utf8(),
                       description="Some Random Team (%s)" % fauxfactory.gen_utf8(),
                       organization=organization.id,)
        obj = organization.get_related('teams').post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list
