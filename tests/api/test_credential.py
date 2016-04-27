import pytest
import fauxfactory
import json
from tests.api import Base_Api_Test
from common.exceptions import BadRequest_Exception


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Credential(Base_Api_Test):
    def test_unicode(self, admin_user, api_credentials_pg):
        '''Create an ssh credential where the password fields contain unicode.'''
        payload = dict(name=fauxfactory.gen_utf8(),
                       description=fauxfactory.gen_utf8(),
                       kind='ssh',
                       user=admin_user.id,
                       username=fauxfactory.gen_alphanumeric(),
                       password=fauxfactory.gen_utf8(),
                       become_method="sudo",
                       become_username=fauxfactory.gen_alphanumeric(),
                       become_password=fauxfactory.gen_utf8())
        credential = api_credentials_pg.post(payload)
        credential.delete()

    @pytest.mark.parametrize("payload, expected_result", [
        (dict(password="foo", username="foo", host="foo"), {"project": ["Project name required for OpenStack credential."]}),
        (dict(project="foo", username="foo", host="foo"), {"password": ["Password or API key required for OpenStack credential."]}),
        (dict(project="foo", password="foo", host="foo"), {"username": ["Username required for OpenStack credential."]}),
        (dict(project="foo", password="foo", username="foo"), {"host": ["Host required for OpenStack credential."]}),
    ], ids=['project', 'password', 'username', 'host'])
    def test_post_invalid_openstack_credential(self, admin_user, api_credentials_pg, payload, expected_result):
        '''
        Tests that if you post an OpenStack credential with missing params that
        the post fails.
        '''
        # create payload
        payload.update(dict(name="openstack-credential-%s" % fauxfactory.gen_utf8(),
                       description="Openstack credential %s" % fauxfactory.gen_utf8(),
                       kind='openstack',
                       user=admin_user.id, ))

        # post payload and verify that exception raised
        exc_info = pytest.raises(BadRequest_Exception, api_credentials_pg.post, payload)
        result = exc_info.value[1]
        assert result == expected_result, "Unexpected response when posting a credential " \
            "with a missing param. %s" % json.dumps(result)
