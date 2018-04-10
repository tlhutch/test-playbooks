import pytest

from towerkit import exceptions as exc
from towerkit import utils

from tests.lib.helpers.rbac_utils import (
    check_user_capabilities,
    check_role_association
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
                with pytest.raises(exc.Forbidden):
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

    def test_superusers_can_change_all_user_passwords(self, all_users):
        new_pass = utils.random_title()
        for user in all_users:
            user.patch(password=new_pass, password_confirm=new_pass)

        for user in all_users:
            with self.current_user(username=user.username, password=new_pass):
                user.get()

    def test_non_superusers_cannot_edit_system_user_passwords(self, factories, non_superusers):
        new_pass = utils.random_title()
        system_users = [factories.v2_user(is_superuser=True), factories.v2_user(is_system_auditor=True)]

        for non_superuser in non_superusers:
            with self.current_user(non_superuser):
                for system_user in system_users:
                    with pytest.raises(exc.Forbidden):
                        system_user.patch(password=new_pass, password_confirm=new_pass)

        for system_user in system_users:
            with self.current_user(system_user):
                system_user.get()

    def test_org_admin_can_only_edit_users_from_own_organization(self, factories, org_users, organization):
        first_pass, second_pass = [utils.random_title() for _ in range(2)]

        org_admin1, org_admin2 = [factories.v2_user() for _ in range(2)]
        organization.add_admin(org_admin1)
        factories.v2_organization().add_admin(org_admin2)

        # org_admin1 should be able to edit users
        for org_user in org_users:
            with self.current_user(org_admin1):
                org_user.patch(password=first_pass, password_confirm=first_pass)

        for org_user in org_users:
            with self.current_user(username=org_user.username, password=first_pass):
                org_user.get()

        # org_admin2 should not be able to edit users
        for org_user in org_users:
            with self.current_user(org_admin2):
                with pytest.raises(exc.Forbidden):
                    org_user.patch(password=second_pass, password_confirm=second_pass)

        for org_user in org_users:
            with self.current_user(username=org_user.username, password=first_pass):
                org_user.get()

    def test_org_admin_can_only_edit_users_if_admin_of_all_target_user_organizations(self, factories, org_users,
                                                                                     organization):
        new_pass = utils.random_title()

        org_admin = factories.v2_user()
        organization.add_admin(org_admin)

        org2 = factories.v2_organization()
        for user in org_users:
            org2.add_user(user)

        # org admin shouldn't be able to edit users
        for org_user in org_users:
            with self.current_user(org_admin):
                with pytest.raises(exc.Forbidden):
                    org_user.patch(password=new_pass, password_confirm=new_pass)

        for org_user in org_users:
            with self.current_user(org_user):
                org_user.get()

        # org admin should now be able to edit users
        org2.add_admin(org_admin)
        for org_user in org_users:
            with self.current_user(org_admin):
                org_user.patch(password=new_pass, password_confirm=new_pass)

        for org_user in org_users:
            with self.current_user(username=org_user.username, password=new_pass):
                org_user.get()

    def test_org_admins_cannot_edit_passwords_of_users_who_are_system_users_and_org_members(self, factories,
                                                                                            system_users):
        new_pass = utils.random_title()

        org = factories.v2_organization()
        org_admin = factories.v2_user()
        org.add_admin(org_admin)

        for system_user in system_users:
            org.add_user(system_user)

        for system_user in system_users:
            with self.current_user(org_admin):
                with pytest.raises(exc.Forbidden):
                    system_user.patch(password=new_pass, password_confirm=new_pass)

        for system_user in system_users:
            with self.current_user(system_user):
                system_user.get()

    def test_all_users_can_change_their_own_password(self, all_users):
        new_pass = utils.random_title()

        for user in all_users:
            with self.current_user(user):
                user.patch(password=new_pass, password_confirm=new_pass)
            with self.current_user(username=user.username, password=new_pass):
                user.get()

    def test_org_admins_can_add_and_remove_orphaned_users_from_their_organization(self, factories):
        org = factories.v2_organization()
        org_admin, orphaned_user = [factories.v2_user() for _ in range(2)]
        org.add_admin(org_admin)

        with self.current_user(org_admin):
            org.add_admin(orphaned_user)
            org.add_user(orphaned_user)

        role_names = ('Admin', 'Member')
        for name in role_names:
            check_role_association(orphaned_user, org, name)

        with self.current_user(org_admin):
            for name in role_names:
                org.set_object_roles(orphaned_user, name, disassociate=True)
        assert orphaned_user.related.roles.get().count == 0
