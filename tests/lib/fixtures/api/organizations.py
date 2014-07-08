import pytest
import common.utils

@pytest.fixture(scope="class")
def organization(request, authtoken, api_organizations_pg):
    payload = dict(name="org-%s" % common.utils.random_unicode(),
                   description="Random organization",)
    obj = api_organizations_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj
