'''
# 1) Verify users with unicode names and passwords
# 2) Verify credentials, owned by the user, are removed upon DELETE
'''

import json
import pytest
import common.utils
import common.exceptions
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def some_user(request, testsetup, authtoken, api_users_pg):
    payload = dict(username="org_admin_%s" % common.utils.random_ascii(),
                   first_name="Joe (%s)" % common.utils.random_unicode(),
                   last_name="User (%s)" % common.utils.random_unicode(),
                   email="org_user_%s@example.com" % common.utils.random_ascii(),
                   password=testsetup.credentials['default']['password'],)
    obj = api_users_pg.post(payload)
    request.addfinalizer(obj.quiet_delete)
    return obj


@pytest.fixture(scope="function")
def some_ssh_credential(request, testsetup, authtoken, api_credentials_pg, some_user):
    '''Create ssh credential'''
    payload = dict(name="credential-%s" % common.utils.random_unicode(),
                   description="machine credential for user:%s" % some_user.username,
                   kind='ssh',
                   user=some_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.quiet_delete)
    return obj


@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Users(Base_Api_Test):
    '''
    Verify the /users endpoint displays the expected information based on the current user
    '''
    pytestmark = pytest.mark.usefixtures('authtoken')

    def test_duplicate(self, api_users_pg, some_user):
        '''Verify that usernames are unique'''
        payload = dict(username=some_user.username,
                       first_name="Another Joe (%s)" % common.utils.random_unicode(),
                       last_name="User (%s)" % common.utils.random_unicode(),
                       email="org_user_%s@example.com" % common.utils.random_ascii(),
                       password=common.utils.random_unicode())
        with pytest.raises(common.exceptions.Duplicate_Exception):
            obj = api_users_pg.post(payload)

    def test_cascade_delete(self, api_credentials_pg, some_user, some_ssh_credential):
        '''Verify that a credentials, owned by a user, are deleted when the user is deleted'''

        # Delete the user
        some_user.delete()

        # Shouldn't be able to query credentials for the deleted user
        with pytest.raises(common.exceptions.Forbidden_Exception):
            some_user.get_related('credentials')

        # Verify that the users credentials were deleted
        remaining_creds = api_credentials_pg.get(id=some_ssh_credential.id)
        assert remaining_creds.count == 0, "The user was deleted, however a credential owned by the user (id:%s) remains" % remaining_creds.results[0].id

        # The credential should have been deleted
        with pytest.raises(common.exceptions.Forbidden_Exception):
            some_ssh_credential.get()

