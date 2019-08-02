import pytest

from awxkit import exceptions as exc
from awxkit import utils

from tests.lib.helpers.rbac_utils import (
    check_user_capabilities,
    check_role_association
)
from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class Test_User_RBAC(APITest):

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

    def test_org_admin_cannot_admin_other_org_admin(self, v2, factories):
        """In the past there was a bug where an admin of one org could add admin of other org to their org.

        This could lead to issue where admin of org a could gain access to org b.

        Only users that already have admin privileges over an org admin can add them to a new org.

        https://github.com/ansible/tower/issues/3480
        """
        org_a, org_b, = [factories.organization() for _ in range(2)]
        admin_a = factories.user(organization=org_a)
        admin_b = factories.user(organization=org_b)
        admin_of_both = factories.user(organization=org_a)
        org_a.add_user(admin_of_both)
        org_a.set_object_roles(admin_a, 'admin')
        org_b.set_object_roles(admin_b, 'admin')
        org_a.set_object_roles(admin_of_both, 'admin')
        org_b.set_object_roles(admin_of_both, 'admin')
        with self.current_user(admin_a):
            active_user = v2.me.get().results.pop()
            assert active_user.username == admin_a.username, "Should be making v2 requests as admin_a!"
            # admin_a should not be allowed to add admin_b to org_a
            # Only a user that already had admin privledges orver admin_b should be allowed to do that
            with pytest.raises(exc.Forbidden):
                org_a.add_user(admin_b)
            with pytest.raises(exc.Forbidden):
                org_a.related.users.post(dict(id=admin_b.id))

        with self.current_user(admin_of_both):
            active_user = v2.me.get().results.pop()
            assert active_user.username == admin_of_both.username, "Should be making v2 requests as admin_of_both!"
            with pytest.raises(exc.NoContent):
                org_a.related.users.post(dict(id=admin_b.id))

        new_pass = utils.random_title()
        with self.current_user(admin_a):
            active_user = v2.me.get().results.pop()
            assert active_user.username == admin_a.username, "Should be making v2 requests as admin_a!"
            # Assert now that admin_b was correctly added by admin_of_both to org_a, admin_a has not
            # gained admin access over user admin_b
            with pytest.raises(exc.Forbidden):
                admin_b.patch(password=new_pass, password_confirm=new_pass)

        with self.current_user(admin_b):
            active_user = v2.me.get().results.pop()
            assert active_user.username == admin_b.username, "Should be making v2 requests as admin_b!"
            # Assert now that admin_b was correctly added by admin_of_both to org_a, admin_b still has admin over themselves
            admin_b.patch(password=new_pass, password_confirm=new_pass)

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
        system_users = [factories.user(is_superuser=True), factories.user(is_system_auditor=True)]

        for non_superuser in non_superusers:
            with self.current_user(non_superuser):
                for system_user in system_users:
                    with pytest.raises(exc.Forbidden):
                        system_user.patch(password=new_pass, password_confirm=new_pass)

        for system_user in system_users:
            with self.current_user(system_user):
                system_user.get()

    @pytest.mark.yolo
    def test_org_admin_can_only_edit_users_from_own_organization(self, factories, org_users, organization):
        first_pass, second_pass = [utils.random_title() for _ in range(2)]

        org_admin1, org_admin2 = [factories.user() for _ in range(2)]
        organization.add_admin(org_admin1)
        factories.organization().add_admin(org_admin2)

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

        org_admin = factories.user()
        organization.add_admin(org_admin)

        org2 = factories.organization()
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

        org = factories.organization()
        org_admin = factories.user()
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
        org = factories.organization()
        org_admin, orphaned_user = [factories.user() for _ in range(2)]
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
