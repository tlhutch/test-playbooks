import pytest
import fauxfactory


@pytest.fixture(scope="function")
def default_organization(authtoken, api_organizations_pg):
    match = api_organizations_pg.get(name='Default')
    assert match.count == 1, "No default organization found (%s)" % match.count
    return match.results.pop()


@pytest.fixture(scope="function")
def organization(request, authtoken, api_organizations_pg):
    fixture_args = getattr(request.function, 'fixture_args', None)
    if fixture_args and fixture_args.kwargs.get('default_organization', False):
        return request.getfuncargvalue('default_organization')
    else:
        payload = dict(name="Random organization %s" % fauxfactory.gen_utf8(),
                       description="Random organization - %s" % fauxfactory.gen_utf8())
        obj = api_organizations_pg.post(payload)
        request.addfinalizer(obj.silent_delete)
        return obj


@pytest.fixture(scope="function")
def another_organization(request, authtoken, api_organizations_pg):
    payload = dict(name="org-%s" % fauxfactory.gen_utf8(),
                   description="Another random organization - %s" % fauxfactory.gen_utf8())
    obj = api_organizations_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def many_organizations(request, authtoken, api_organizations_pg):
    obj_list = list()
    for i in range(55):
        payload = dict(name="%s random %s organization" % (i, fauxfactory.gen_utf8()),
                       description="Random organization %s %s" % (i, fauxfactory.gen_utf8()))
        obj = api_organizations_pg.post(payload)
        request.addfinalizer(obj.silent_delete)
        obj_list.append(obj)
    return obj_list
