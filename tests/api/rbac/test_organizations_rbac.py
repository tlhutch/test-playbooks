import pytest
import httplib

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_user_capabilities,
    set_roles
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_Organization_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        """An unprivileged user should not be able to:
        * Issue GETs to our organization details page
        * Issue GETs to all of this organization's related pages
        * Edit our organization
        * Delete our organization
        """
        organization_pg = factories.organization()
        user_pg = factories.user()

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.FORBIDDEN)

    def test_auditor_role(self, factories, user_password):
        """A user with organization 'auditor' should be able to:
        * Issue GETs to our organization details page
        * Issue GETs to all of this organization's related pages
        A user with organization 'auditor' should not be able to:
        * Edit our organization
        * Delete our organization
        """
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user auditor privileges
        set_roles(user_pg, organization_pg, ['auditor'])

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.FORBIDDEN)

    def test_admin_role(self, factories, user_password):
        """A user with organization 'admin' should be able to:
        * GET our organization details page
        * GET all of our organization's related pages
        * Edit our organization
        * Delete our organization
        """
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user admin privileges
        set_roles(user_pg, organization_pg, ['admin'])

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.OK)

    def test_member_role(self, factories, user_password):
        """A user with organization 'member' should be able to:
        * The ability to make a GET to our target organization
        * The ability to make a GET against our organization's related endpoints
        A user with organization 'member' should not be able to:
        * Edit our organization
        * Delete our organization
        """
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user member privileges
        set_roles(user_pg, organization_pg, ['member'])

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.FORBIDDEN)

    def test_read_role(self, factories, user_password):
        """A user with organization 'read' should be able to:
        * The ability to make a GET to our target organization
        * The ability to make a GET against our organization's related endpoints
        A user with organization 'read' should not be able to:
        * Edit our organization
        * Delete our organization
        """
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user read role privileges
        set_roles(user_pg, organization_pg, ['read'])

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'auditor', 'member', 'read'])
    def test_user_capabilities(self, factories, user_password, api_organizations_pg, role):
        """Test user_capabilities given each organization role."""
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, organization_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(organization_pg.get(), role)
            check_user_capabilities(api_organizations_pg.get(id=organization_pg.id).results.pop(), role)

    def test_org_admin_job_deletion(self, factories):
        """Test that org admins can delete jobs from their organization only."""
        org = factories.organization()
        org_admin = factories.user()
        org.add_admin(org_admin)

        project = factories.project(organization=org)
        jt1 = factories.job_template(project=project)
        jt2 = factories.job_template()

        job1 = jt1.launch().wait_until_completed()
        job2 = jt2.launch().wait_until_completed()

        with self.current_user(username=org_admin.username, password=org_admin.password):
            job1.delete()
            with pytest.raises(towerkit.exceptions.Forbidden):
                job2.delete()

    def test_org_admin_command_deletion(self, factories, v1):
        """Test that org admins can delete commands from their organization only."""
        org = factories.organization()
        org_admin = factories.user()
        org.add_admin(org_admin)

        inv1 = factories.inventory(organization=org)
        inv2 = factories.inventory()

        ahc1 = v1.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=inv1)
        ahc2 = v1.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=inv2)

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

        # launch inventory updates
        inv_update1 = group1.related.inventory_source.get().update().wait_until_completed()
        inv_update2 = group2.related.inventory_source.get().update().wait_until_completed()

        with self.current_user(username=org_admin.username, password=org_admin.password):
            inv_update1.delete()
            with pytest.raises(towerkit.exceptions.Forbidden):
                inv_update2.delete()

    def test_member_role_association(self, factories, user_password):
        """Tests that after a user is granted member_role that he now shows
        up under organizations/N/users.
        """
        user_pg = factories.user()
        organization_pg = factories.organization()

        # organization by default should have no users
        users_pg = organization_pg.get_related('users')
        assert users_pg.count == 0, "%s user[s] unexpectedly found for organization/%s." % (users_pg.count, organization_pg.id)

        # give test user member role privileges
        set_roles(user_pg, organization_pg, ["member"])

        # assert that organizations/N/users now shows test user
        assert users_pg.get().count == 1, "Expected one user for organization/%s/users/, got %s." % (organization_pg.id, users_pg.count)
        assert users_pg.results[0].id == user_pg.id, \
            "Organization user not our target user. Expected user with ID %s but got one with ID %s." % (user_pg.id, users_pg.results[0].id)

    def test_autopopulated_member_role(self, organization, org_user, user_password):
        """Tests that when you create a user by posting to organizations/N/users
        that the user is automatically created with a member_role for this
        organization.
        """
        # assert test user created in target organization
        organizations_pg = org_user.get_related('organizations')
        assert organizations_pg.count == 1, \
            "Unexpected number of organizations returned. Expected 1, got %s." % organizations_pg.count
        assert organizations_pg.results[0].id == organization.id, \
            "org_user not created in organization/%s." % organization.id

        # assert test user created with member_role
        roles_pg = org_user.get_related('roles')
        assert roles_pg.count == 1, \
            "Unexpected number of roles returned. Expected 1, got %s." % roles_pg.count
        role_pg = roles_pg.results[0]
        assert role_pg.id == organization.get_object_role('member_role').id, \
            "Unexpected user role returned. Expected %s, got %s." % (organization.get_object_role('member_role').id, role_pg.id)

    @pytest.mark.parametrize('organization_role', ['admin_role', 'auditor_role', 'member_role', 'read_role'])
    def test_organization_roles_not_allowed_with_teams(self, factories, organization_role):
        """Test that an organization role association with a team raises a 400."""
        team_pg = factories.team()
        organization_pg = factories.organization()

        # attempt role association
        role_pg = organization_pg.get_object_role(organization_role)
        payload = dict(id=role_pg.id)

        exc_info = pytest.raises(towerkit.exceptions.BadRequest, team_pg.get_related('roles').post, payload)
        result = exc_info.value[1]
        assert result == {u'msg': u'You cannot assign an Organization role as a child role for a Team.'}, \
            "Unexpected error message received when attempting to assign an organization role to a team."

    @pytest.mark.parametrize('role', ['admin', 'auditor', 'member', 'read'])
    def test_change_project_org_affiliation(self, factories, role):
        """Confirm attempts to change project org to an unaffiliated one result in 403 for all organization roles"""
        org = factories.organization()
        project = factories.project(organization=org, wait=False)
        user = factories.user()
        another_org = factories.organization()

        org.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                project.organization = another_org.id
