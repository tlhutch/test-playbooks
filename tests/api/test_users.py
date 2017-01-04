import json
import pytest
import fauxfactory
import towerkit.exceptions
from tests.api import Base_Api_Test


def user_payload(**kwargs):
    """
    Convenience function to return a API payload for use with posting to
    /api/v1/users/.
    """
    payload = dict(username="joe_user_%s" % fauxfactory.gen_alphanumeric(),
                   first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                   last_name="User (%s)" % fauxfactory.gen_utf8(),
                   email=fauxfactory.gen_email(),
                   password=kwargs.get('password', 'password'))
    if 'is_superuser' in kwargs:
        payload['is_superuser'] = kwargs.get('is_superuser')
    return payload


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Users(Base_Api_Test):
    """
    Verify the /users/ endpoint displays the expected information based on the current user.
    """
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_duplicate(self, api_users_pg, anonymous_user):
        """Verify that usernames are unique."""
        payload = dict(username=anonymous_user.username,
                       first_name="Another Joe (%s)" % fauxfactory.gen_utf8(),
                       last_name="User (%s)" % fauxfactory.gen_utf8(),
                       email=fauxfactory.gen_email(),
                       password=fauxfactory.gen_utf8())
        with pytest.raises(towerkit.exceptions.Duplicate):
            api_users_pg.post(payload)

    def test_superuser_can_create_superuser(self, superuser):
        """
        Verify that a superuser can create other superusers.

        Note: 'superuser' creation upon test setup is performed by admin user.
        """
        assert superuser.is_superuser, "Failed to create a superuser."

    def test_org_admin_cannot_create_a_superuser(self, request, org_admin, user_password):
        """
        Verify that org_admins cannot create superusers via the organization users_pg.
        """
        users_pg = org_admin.get_related('organizations').results[0].get_related('users')

        # Test various ways of passing is_superuser
        with self.current_user(org_admin.username, user_password):
            for is_superuser in (None, False, 'false', 'False', 'f', 0, '0'):
                payload = user_payload(is_superuser=is_superuser)
                print json.dumps(payload, indent=2)
                obj = users_pg.post(payload)
                request.addfinalizer(obj.delete)
                assert not obj.is_superuser, "Unexpectedly created a superuser with the following payload\n%s." % json.dumps(obj.json, indent=2)

    def test_non_superuser_cannot_elevate_themselves_to_superuser(self, non_superuser, user_password):
        """
        Verify that non-superusers cannot elevate their privileges by issuing a
        PATCH or PUT request with is_superuser=True.
        """
        with self.current_user(non_superuser.username, user_password):
            # assert a non-superuser cannot elevate themselves to superuser with patch
            with pytest.raises(towerkit.exceptions.Forbidden):
                non_superuser.patch(is_superuser=True)

            # assert a non-superuser cannot elevate themselves to superuser with put
            with pytest.raises(towerkit.exceptions.Forbidden):
                non_superuser.json['is_superuser'] = True
                non_superuser.put(non_superuser.json)

    def test_org_member_cannot_elevate_themselves_to_org_admin(self, org_user, user_password):
        """
        Verifies that an org_member cannot elevate himself to an org_admin by associating himself
        via /api/v1/organizations/N/admins/.
        """
        org_admin_pg = org_user.get_related('organizations').results[0].get_related('admins')

        with self.current_user(org_user.username, user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                payload = dict(id=org_user.id)
                org_admin_pg.post(payload)

    def test_org_admin_can_create_org_user(self, request, org_admin, user_password):
        """
        Verify that an org_admin can create org_users.
        """
        users_pg = org_admin.get_related('organizations').results[0].get_related('users')

        with self.current_user(org_admin.username, user_password):
            obj = users_pg.post(user_payload())
            request.addfinalizer(obj.delete)

    def test_org_member_cannot_create_org_user(self, org_user, user_password):
        """
        Verify that an org_user cannot create additional org_users.
        """
        users_pg = org_user.get_related('organizations').results[0].get_related('users')

        with self.current_user(org_user.username, user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                users_pg.post(user_payload())

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/4293", raises=towerkit.exceptions.Forbidden)
    def test_nonsuperusers_cannot_create_orphaned_user(self, api_users_pg, non_superuser, user_password):
        """
        Verify that a non_superuser cannot create users via /api/v1/users/.
        """
        with self.current_user(non_superuser.username, user_password):
            with pytest.raises(towerkit.exceptions.MethodNotAllowed):
                api_users_pg.post(user_payload())
