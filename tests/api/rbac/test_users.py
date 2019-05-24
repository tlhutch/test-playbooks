import json

import towerkit.exceptions as exc
import fauxfactory
import pytest

from tests.api import APITest


def user_payload(**kwargs):
    """Convenience function to return a API payload for use with posting to
    /api/v2/users/.
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
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Users(APITest):

    def test_duplicate_users_disallowed(self, factories):
        user = factories.v2_user()

        with pytest.raises(exc.Duplicate) as e:
            factories.user(username=user.username)
        assert e.value[1]['username'] == ['A user with that username already exists.']

    def test_superuser_can_create_superuser(self, superuser):
        """Verify that a superuser can create other superusers.

        Note: 'superuser' creation upon test setup is performed by admin user.
        """
        assert superuser.is_superuser, "Failed to create a superuser."

    def test_org_admin_cannot_create_a_superuser(self, request, org_admin, user_password):
        """Verify that org_admins cannot create superusers via the organization users_pg."""
        users_pg = org_admin.get_related('organizations').results[0].get_related('users')

        # Test various ways of passing is_superuser
        with self.current_user(org_admin.username, user_password):
            for is_superuser in (None, False, 'false', 'False', 'f', 0, '0'):
                payload = user_payload(is_superuser=is_superuser)
                print(json.dumps(payload, indent=2))
                obj = users_pg.post(payload)
                request.addfinalizer(obj.delete)
                assert not obj.is_superuser, "Unexpectedly created a superuser with the following payload\n%s." % json.dumps(obj.json, indent=2)

    def test_non_superuser_cannot_elevate_themselves_to_superuser(self, non_superuser, user_password):
        """Verify that non-superusers cannot elevate their privileges by issuing a
        PATCH or PUT request with is_superuser=True.
        """
        with self.current_user(non_superuser.username, user_password):
            # assert a non-superuser cannot elevate themselves to superuser with patch
            with pytest.raises(exc.Forbidden):
                non_superuser.patch(is_superuser=True)

            # assert a non-superuser cannot elevate themselves to superuser with put
            with pytest.raises(exc.Forbidden):
                non_superuser.json['is_superuser'] = True
                non_superuser.put(non_superuser.json)

    def test_org_member_cannot_elevate_themselves_to_org_admin(self, org_user, user_password):
        """Verifies that an org_member cannot elevate himself to an org_admin by associating himself
        via /api/v2/organizations/N/admins/.
        """
        org_admin_pg = org_user.get_related('organizations').results[0].get_related('admins')

        with self.current_user(org_user.username, user_password):
            with pytest.raises(exc.Forbidden):
                payload = dict(id=org_user.id)
                org_admin_pg.post(payload)

    def test_org_admin_can_create_org_user(self, request, org_admin, user_password):
        """Verify that an org_admin can create org_users."""
        users_pg = org_admin.get_related('organizations').results[0].get_related('users')

        with self.current_user(org_admin.username, user_password):
            obj = users_pg.post(user_payload())
            request.addfinalizer(obj.delete)

    def test_org_member_cannot_create_org_user(self, org_user, user_password):
        """Verify that an org_user cannot create additional org_users."""
        users_pg = org_user.get_related('organizations').results[0].get_related('users')

        with self.current_user(org_user.username, user_password):
            with pytest.raises(exc.Forbidden):
                users_pg.post(user_payload())

    def test_nonsuperusers_cannot_create_orphaned_user(self, api_users_pg, non_superuser, user_password):
        """Verify that a non_superuser cannot create users via /api/v2/users/."""
        with self.current_user(non_superuser.username, user_password):
            with pytest.raises(exc.Forbidden):
                api_users_pg.post(user_payload())

    def test_user_creation_doesnt_leak_password_into_activity_stream(self, v2, factories):
        superuser = factories.v2_user(is_superuser=True)
        user_activity_stream = str(superuser.related.activity_stream.get())
        for secret in (superuser.password, 'md5'):
            assert secret not in user_activity_stream
