import pytest
import fauxfactory
import json
from tests.api import Base_Api_Test
from common.exceptions import BadRequest_Exception


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_OpenStack_Credential(Base_Api_Test):
    @pytest.mark.parametrize("payload, expected_result", [
        (dict(password="foo", username="foo", host="foo"), {"project": ["Project name required for OpenStack credential."]}),
        (dict(project="foo", username="foo", host="foo"), {"password": ["Password required for OpenStack credential."]}),
        (dict(project="foo", password="foo", host="foo"), {"username": ["Username name required for OpenStack credential."]}),
        (dict(project="foo", password="foo", username="foo"), {"host": ["Host required for OpenStack credential."]}),
    ])
    def test_post_invalid_credential(self, admin_user, api_credentials_pg, payload, expected_result):
        '''
        Tests that if you post an OpenStack credential with mising params that
        the post fails.
        '''
        # create payload
        payload.update(dict(name="openstack-credential-%s" % fauxfactory.gen_utf8(),
                       description="Openstack credential %s" % fauxfactory.gen_utf8(),
                       kind='openstack',
                       user=admin_user.id, ))

        exc_info = pytest.raises(BadRequest_Exception, api_credentials_pg.post, payload)
        result = exc_info.value[1]

        # post payload and verify that exception raised
        assert result == expected_result, "Unexpected response when posting a credential " \
            "with a missing param. %s" % json.dumps(result)
