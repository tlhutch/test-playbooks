import pytest
import common.utils


@pytest.fixture(scope="class")
def organization(request, authtoken, api_organizations_pg):
    payload = dict(name="org-%s" % common.utils.random_unicode(),
                   description="Random organization - %s" % common.utils.random_unicode())
    obj = api_organizations_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="class")
def another_organization(request, authtoken, api_organizations_pg):
    payload = dict(name="org-%s" % common.utils.random_unicode(),
                   description="Another random organization - %s" % common.utils.random_unicode())
    obj = api_organizations_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def many_organizations(request, authtoken, api_organizations_pg):

    obj_list = list()
    for i in range(55):
        payload = dict(name="%s random %s organization" % (i, common.utils.random_unicode()),
                       description="Random organization %s %s" % (i, common.utils.random_unicode()))
        obj = api_organizations_pg.post(payload)
        request.addfinalizer(obj.silent_delete)
        obj_list.append(obj)
    return obj_list
