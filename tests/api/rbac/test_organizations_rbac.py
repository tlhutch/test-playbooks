import pytest
import httplib

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_user_capabilities
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Organization_RBAC(Base_Api_Test):

    def test_unprivileged_user(self, factories):
        """An unprivileged user should not be able to:
        * Issue GETs to our organization details page
        * Issue GETs to all of this organization's related pages
        * Edit our organization
        * Delete our organization
        """
        organization = factories.organization()
        user = factories.user()

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(organization, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(organization, httplib.FORBIDDEN)

    def test_auditor_role(self, factories):
        """A user with organization 'auditor' should be able to:
        * Issue GETs to our organization details page
        * Issue GETs to all of this organization's related pages
        A user with organization 'auditor' should not be able to:
        * Edit our organization
        * Delete our organization
        """
        organization = factories.organization()
        user = factories.user()

        organization.set_object_roles(user, "auditor")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(organization)

            # check put/patch/delete
            assert_response_raised(organization, httplib.FORBIDDEN)

    def test_admin_role(self, factories):
        """A user with organization 'admin' should be able to:
        * GET our organization details page
        * GET all of our organization's related pages
        * Edit our organization
        * Delete our organization
        """
        organization = factories.organization()
        user = factories.user()

        organization.set_object_roles(user, "admin")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(organization)

            # check put/patch/delete
            assert_response_raised(organization, httplib.OK)

    def test_member_role(self, factories):
        """A user with organization 'member' should be able to:
        * The ability to make a GET to our target organization
        * The ability to make a GET against our organization's related endpoints
        A user with organization 'member' should not be able to:
        * Edit our organization
        * Delete our organization
        """
        organization = factories.organization()
        user = factories.user()

        organization.set_object_roles(user, "member")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(organization)

            # check put/patch/delete
            assert_response_raised(organization, httplib.FORBIDDEN)

    def test_read_role(self, factories):
        """A user with organization 'read' should be able to:
        * The ability to make a GET to our target organization
        * The ability to make a GET against our organization's related endpoints
        A user with organization 'read' should not be able to:
        * Edit our organization
        * Delete our organization
        """
        organization = factories.organization()
        user = factories.user()

        organization.set_object_roles(user, "read")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(organization)

            # check put/patch/delete
            assert_response_raised(organization, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'auditor', 'member', 'read'])
    def test_user_capabilities(self, factories, api_organizations_pg, role):
        """Test user_capabilities given each organization role."""
        organization = factories.organization()
        user = factories.user()

        organization.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(organization.get(), role)
            check_user_capabilities(api_organizations_pg.get(id=organization.id).results.pop(), role)

    def test_org_admin_job_deletion(self, factories):
        """Test that org admins can delete jobs from their organization only."""
        org = factories.organization()
        org_admin = factories.user()
        org.add_admin(org_admin)

        # run JT organization is determined by its project
        project = factories.project(organization=org)
        jt1 = factories.job_template(project=project)
        jt2 = factories.job_template()

        job1 = jt1.launch().wait_until_completed()
        job2 = jt2.launch().wait_until_completed()

        with self.current_user(username=org_admin.username, password=org_admin.password):
            job1.delete()
            with pytest.raises(towerkit.exceptions.Forbidden):
                job2.delete()

    def test_org_admin_command_deletion(self, factories):
        """Test that org admins can delete commands from their organization only."""
        org = factories.organization()
        org_admin = factories.user()
        org.add_admin(org_admin)

        inv1 = factories.inventory(organization=org)
        inv2 = factories.inventory()

        # ahc organization is determined by its inventory
        ahc1, ahc2 = [factories.ad_hoc_command(module_name='shell', module_args='true', inventory=inv).wait_until_completed()
                      for inv in (inv1, inv2)]

        with self.current_user(username=org_admin.username, password=org_admin.password):
            ahc1.delete()
            with pytest.raises(towerkit.exceptions.Forbidden):
                ahc2.delete()

    def test_org_admin_project_update_deletion(self, factories):
        """Test that org admins can delete project updates from their organization only."""
        org = factories.organization()
        org_admin = factories.user()
        org.add_admin(org_admin)

        project1 = factories.project(organization=org)
        project2 = factories.project()

        update1 = project1.update().wait_until_completed()
        update2 = project2.update().wait_until_completed()

        with self.current_user(username=org_admin.username, password=org_admin.password):
            update1.delete()
            with pytest.raises(towerkit.exceptions.Forbidden):
                update2.delete()

    def test_org_admin_inventory_update_deletion(self, factories):
        """Test that org admins can delete inventory updates from their organization only."""
        org1 = factories.organization()
        org2 = factories.organization()
        org_admin = factories.user()
        org1.add_admin(org_admin)

        inv1 = factories.inventory(organization=org1)
        inv2 = factories.inventory(organization=org2)

        # create custom groups
        inv_script1 = factories.inventory_script(organization=org1)
        inv_script2 = factories.inventory_script(organization=org2)
        group1 = factories.group(inventory=inv1, inventory_script=inv_script1)
        group2 = factories.group(inventory=inv2, inventory_script=inv_script2)

        inv_update1 = group1.related.inventory_source.get().update().wait_until_completed()
        inv_update2 = group2.related.inventory_source.get().update().wait_until_completed()

        with self.current_user(username=org_admin.username, password=org_admin.password):
            inv_update1.delete()
            with pytest.raises(towerkit.exceptions.Forbidden):
                inv_update2.delete()

    def test_member_role_association(self, factories):
        """Tests that after a user is granted member_role that he now shows
        up under /organizations/N/users/.
        """
        user = factories.user()
        organization = factories.organization()

        # organization by default should have no users
        users = organization.related.users.get()
        assert users.count == 0, "%s user[s] unexpectedly found for our organization." % users.count

        organization.set_object_roles(user, "member")

        # assert that /organizations/N/users/ now shows our test user
        assert users.get().count == 1, "Expected one user under /organization/N/users/, got %s." % users.count
        assert users.results[0].id == user.id, \
            "Expected user with ID %s but got one with ID %s." % (user.id, users.results[0].id)

    def test_autopopulated_member_role(self, organization, org_user):
        """Tests that when you create a user by posting to /organizations/N/users/
        that the user is automatically created with the member role for this
        organization.
        """
        # assert test user created in target organization
        organizations = org_user.related.organizations.get()
        assert organizations.count == 1, \
            "Unexpected number of organizations returned. Expected one, got %s." % organizations.count
        assert organizations.results[0].id == organization.id, \
            "Organization user not created in target organization."

        # assert test user created with member_role
        roles = org_user.related.roles.get()
        assert roles.count == 1, \
            "Unexpected number of roles returned. Expected one, got %s." % roles.count
        role = roles.results[0]
        assert role.id == organization.get_object_role('member_role').id, \
            "Unexpected user role returned (member role expected)."

    @pytest.mark.parametrize('role', ['admin', 'auditor', 'member', 'read'])
    def test_organization_roles_not_allowed_with_teams(self, factories, role):
        """Test that an organization role association with a team raises a 400."""
        team = factories.team()
        organization = factories.organization()

        with pytest.raises(towerkit.exceptions.BadRequest):
            organization.set_object_roles(team, role)
