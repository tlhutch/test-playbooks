import types

import pytest
import fauxfactory


@pytest.fixture(scope="function")
def default_organization(api_organizations_pg):
    matches = api_organizations_pg.get(name='Default')
    assert matches.count == 1, "Default organization not found."
    org = matches.results.pop()

    # Protect from inadvertantly deleting the default organization
    def protect_from_delete(self):
        pass
    org.delete = types.MethodType(protect_from_delete, org)
    return org


@pytest.fixture(scope="function")
def organization(request, api_config_pg, factories):
    if 'multiple_organizations' not in api_config_pg.get().features:
        return request.getfixturevalue('default_organization')
    else:
        org = factories.organization(name="Random organization %s" % fauxfactory.gen_utf8(),
                                     description="Random organization - %s" % fauxfactory.gen_utf8())
        return org


@pytest.fixture(scope="function")
def another_organization(factories):
    org = factories.organization(name="Another random organization %s" % fauxfactory.gen_utf8(),
                                 description="Another random organization - %s" % fauxfactory.gen_utf8())
    return org
