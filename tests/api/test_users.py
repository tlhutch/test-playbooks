'''
# 1) Verify users with unicode names and passwords
# 2) Verify credentials, owned by the user, are removed upon DELETE
'''

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
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def some_ssh_credential(request, testsetup, authtoken, some_user):
    '''Create ssh credential'''
    payload = dict(name="credential-%s" % common.utils.random_unicode(),
                   description="machine credential for user:%s" % some_user.username,
                   kind='ssh',
                   user=some_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)
    obj = some_user.get_related('credentials').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def org_users(request, org_admin, org_user):
    return (org_admin, org_user)


@pytest.fixture(scope="function")
def non_org_users(request, anonymous_user, another_org_admin, another_org_user):
    return (anonymous_user, another_org_admin, another_org_user)


@pytest.mark.api
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
            api_users_pg.post(payload)

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
        with pytest.raises(common.exceptions.NotFound_Exception):
            some_ssh_credential.get()

    def test_org_admins_can_see_all_users(self, user_password, api_users_pg, org_admin, org_users, non_org_users):
        '''
        Verify the default behavior where a Tower org admin can see users
        outside their organization.
        '''
        with self.current_user(org_admin.username, user_password):
            # find users within current organization
            matching_org_users = api_users_pg.get(
                username__in=','.join([u.username for u in org_users]))

            # assert user visibility
            assert matching_org_users.count == len(org_users), \
                "An Org Admin is unable to see users (%s) within the " \
                "same organization." % \
                (matching_org_users.count,)

            # find users outside current organization
            matching_non_org_users = api_users_pg.get(
                username__in=','.join([u.username for u in non_org_users]))

            # assert user visibility
            assert matching_non_org_users.count == len(non_org_users), \
                "An Org Admin is unable to see users (%s) outside the " \
                "organization, despite the default setting " \
                "ORG_ADMINS_CAN_SEE_ALL_USERS:True" % \
                (matching_non_org_users.count,)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Org_Admin(Base_Api_Test):
    '''
    Verify the behavior where a Tower org admin cannot see users outside their
    organization.  Requires setting the following tower variable:

    > ORG_ADMINS_CANNOT_SEE_ALL_USERS = False

    Trello: https://trello.com/c/M74W11hQ
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'ORG_ADMINS_CANNOT_SEE_ALL_USERS')

    def test_org_admins_cannot_see_all_users(self, user_password, api_users_pg, org_admin, org_users, non_org_users):
        '''
        Verify that an organization admin can only see users within the organization.
        '''
        with self.current_user(org_admin.username, user_password):
            # find users within current organization
            matching_org_users = api_users_pg.get(
                username__in=','.join([u.username for u in org_users]))

            # assert user visibility
            assert matching_org_users.count == len(org_users), \
                "An Org Admin is unable to see users (%s) within the " \
                "same organization." % \
                (matching_org_users.count,)

            # find users outside current organization
            matching_non_org_users = api_users_pg.get(
                username__in=','.join([u.username for u in non_org_users]))

            # assert user visibility
            assert matching_non_org_users.count == 0, \
                "An Org Admin is able to see users (%s) outside the " \
                "organization, despite the setting " \
                "ORG_ADMINS_CAN_SEE_ALL_USERS:False" % \
                (matching_non_org_users.count,)
