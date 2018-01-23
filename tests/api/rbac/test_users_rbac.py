import pytest

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    check_user_capabilities
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_User_RBAC(Base_Api_Test):

    def test_user_admin_role_application_forbidden(self, factories, api_roles_pg):
        """Confirms that users are not able to have any admin role (dis)associated with themselves."""
        user_one, user_two = [factories.user() for _ in range(2)]
        user_one_admin_role = api_roles_pg.get(object_id=user_one.id,
                                               role_field='admin_role',
                                               members__in=user_one.id).results[0]

        for user in [user_one, user_two]:
            for disassociate in [True, False]:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    user.related.roles.post(dict(id=user_one_admin_role.id,
                                                 disassociate=disassociate))

    def test_user_capabilities_as_superuser(self, factories, api_users_pg):
        """Tests 'user_capabilities' with a superuser."""
        superuser = factories.user(is_superuser=True)

        check_user_capabilities(superuser, "superuser")
        check_user_capabilities(api_users_pg.get(id=superuser.id).results.pop(), "superuser")

    def test_user_capabilities_as_org_admin(self, factories, api_users_pg):
        """Tests 'user_capabilities' with an org_admin."""
        organization = factories.organization()
        org_user = factories.user()
        org_admin = factories.user()

        organization.set_object_roles(org_user, "member")
        organization.set_object_roles(org_admin, "admin")

        with self.current_user(username=org_admin.username, password=org_admin.password):
            check_user_capabilities(org_user.get(), "org_admin")
            check_user_capabilities(api_users_pg.get(id=org_user.id).results.pop(), "org_admin")

    def test_cross_org_admin_self_rename(self, factories):
        """Confirms that a user who is a member of one org and an admin of another can change their own name"""
        org_a, org_b, = [factories.organization() for _ in range(2)]
        user = factories.user(organization=org_a)
        org_b.set_object_roles(user, 'admin')
        with self.current_user(user.username, user.password):
            user.first_name = 'First'
            user.last_name = 'Last'
        assert(user.get().first_name == 'First')
        assert(user.last_name == 'Last')

    def test_all_users_can_change_their_own_password(self, all_users):
        new_pass = "new_password"

        for user in all_users:
            with self.current_user(user):
                user.patch(password=new_pass, password_confirm=new_pass)
            with self.current_user(username=user.username, password=new_pass):
                user.get()
