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
