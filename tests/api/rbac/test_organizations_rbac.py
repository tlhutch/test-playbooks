from collections import namedtuple

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

    ResourceMapping = namedtuple('ResourceMapping', [
        'resource_role', 'resource_type'])

    org_resource_admin_mappings = [
        ResourceMapping(resource_role='Inventory Admin',
                        resource_type='inventory'),
        ResourceMapping(resource_role='Project Admin',
                        resource_type='project'),
        ResourceMapping(resource_role='Notification Admin',
                        resource_type='notification_template'),
        ResourceMapping(resource_role='Credential Admin',
                        resource_type='credential'),
        ResourceMapping(resource_role='Workflow Admin',
                        resource_type='workflow_job_template'),
        ResourceMapping(resource_role='Job Template Admin',
                        resource_type='job_template'),
    ]

    def mapping_id(param):
        return param.resource_role

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
            check_user_capabilities(api_organizations_pg.get(
                id=organization.id).results.pop(), role)

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
            "Expected user with ID %s but got one with ID %s." % (
                user.id, users.results[0].id)

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

    @pytest.mark.parametrize('role', ['admin', 'member'])
    def test_organization_roles_not_allowed_with_teams(self, factories, role):
        """Test that an organization role association with a team raises a 400."""
        team = factories.team()
        organization = factories.organization()

        with pytest.raises(towerkit.exceptions.BadRequest):
            organization.set_object_roles(team, role)

    @staticmethod
    def create_resource(factories, res_type, org):
        if res_type == 'job_template':
            # Would like to specify kwargs like 'project': (Project, {Organization: org})
            # but something about the towerkit dependency store does not work for that
            kwargs = {
                'project': factories.v2_project(organization=org),
                'inventory': factories.v2_inventory(organization=org),
                'credential': factories.v2_credential(organization=org)
            }
        else:
            kwargs = {'organization': org}
        return getattr(factories, 'v2_{}'.format(res_type))(**kwargs)

    @pytest.mark.parametrize('resource_mapping', org_resource_admin_mappings, ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_organization_resource_admins_can_create_resources(self, factories, resource_mapping, agent, set_test_roles):
        org = factories.organization()
        resource_admin = factories.user()
        if resource_mapping.resource_role == 'Job Template Admin':
            # Documented specicial behavior for job template creation
            set_test_roles(resource_admin, org, agent, 'Inventory Admin')
            set_test_roles(resource_admin, org, agent, 'Project Admin')
            set_test_roles(resource_admin, org, agent, 'Credential Admin')
        else:
            set_test_roles(resource_admin, org, agent, resource_mapping.resource_role)
        with self.current_user(resource_admin):
            self.create_resource(factories, resource_mapping.resource_type, org)

    @pytest.mark.parametrize('resource_mapping', org_resource_admin_mappings, ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_organization_resource_admins_can_modify_resources(self, factories, resource_mapping, agent, set_test_roles):
        """Test that the resource admin can modify and delete for organization resources that they did not create."""
        org = factories.organization()
        resource_admin = factories.user()

        set_test_roles(resource_admin, org, agent, resource_mapping.resource_role)

        resource = self.create_resource(factories, resource_mapping.resource_type, org)

        with self.current_user(resource_admin):
            assert_response_raised(resource, httplib.OK)

    @pytest.mark.parametrize('resource_mapping',
                             [m for m in org_resource_admin_mappings
                              if m.resource_type != 'notification_template'],
                             ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_organization_resource_admins_can_grant_permissions_to_internal_users(self, factories, resource_mapping, agent, set_test_roles):
        org = factories.organization()
        resource_admin, user = [factories.v2_user(
            organization=o) for o in (None, org)]
        set_test_roles(resource_admin, org, agent, resource_mapping.resource_role)

        resource = self.create_resource(factories, resource_mapping.resource_type, org)

        with self.current_user(resource_admin):
            resource.set_object_roles(user, 'admin')

    @pytest.mark.parametrize('resource_mapping',
                             [m for m in org_resource_admin_mappings if
                              m.resource_type != 'notification_template'],
                             ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_organization_resource_admins_cannot_grant_permissions_to_external_users(self, factories, resource_mapping, agent, set_test_roles):
        org = factories.organization()
        resource_admin, user = [factories.v2_user(
            organization=o) for o in (None, None)]
        set_test_roles(resource_admin, org, agent, resource_mapping.resource_role)

        resource = self.create_resource(factories, resource_mapping.resource_type, org)

        with self.current_user(resource_admin):
            if resource_mapping.resource_type == 'credential':
                # Credentials use a different exception
                with pytest.raises(towerkit.exceptions.BadRequest):
                    resource.set_object_roles(user, 'admin')
            else:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    resource.set_object_roles(user, 'admin')

    @pytest.mark.parametrize('resource_mapping', org_resource_admin_mappings, ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_organization_resource_admins_cannot_modify_resources_in_other_orgs(self, factories, resource_mapping, agent, set_test_roles):
        org1, org2 = [factories.v2_organization() for _ in range(2)]
        resource_admin, user = [factories.v2_user(
            organization=o) for o in (None, org2)]

        set_test_roles(resource_admin, org1, agent, resource_mapping.resource_role)

        resource = self.create_resource(factories, resource_mapping.resource_type, org2)

        with self.current_user(resource_admin):
            if resource_mapping.resource_type != 'notification_template':
                # Skip notification_templates because they do not have object-level permissions
                with pytest.raises(towerkit.exceptions.Forbidden):
                    resource.set_object_roles(user, 'admin')
            assert_response_raised(resource, httplib.FORBIDDEN)

    @pytest.mark.parametrize('resource_mapping',
                             org_resource_admin_mappings,
                             ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_resource_permissions_are_deescalated_after_disassociating(self, factories, resource_mapping, agent, set_test_roles):
        """Grant a user resource admin rights, create a resource, remove user's role, and verify
        that they are not able to modify the resource"""
        org = factories.organization()
        resource_admin, user = [factories.v2_user(
            organization=org) for _ in range(2)]
        team = set_test_roles(resource_admin, org, agent, resource_mapping.resource_role)

        resource = self.create_resource(factories, resource_mapping.resource_type, org)

        set_test_roles(resource_admin, org, agent, resource_mapping.resource_role, team=team, disassociate=True)
        with self.current_user(resource_admin):
            if resource_mapping.resource_type != 'notification_template':
                # Skip notification_templates because they do not have object-level permissions
                with pytest.raises(towerkit.exceptions.Forbidden):
                    resource.set_object_roles(user, 'admin')
            assert_response_raised(resource, httplib.FORBIDDEN)

    def test_workflow_admins_cannot_add_templates_to_workflows_without_permission(self, factories):
        org = factories.v2_organization()
        workflow_admin = factories.v2_user()
        org.set_object_roles(workflow_admin, 'Workflow Admin')

        inv = factories.v2_inventory(organization=org)
        jt = factories.v2_job_template(inventory=inv)

        with self.current_user(workflow_admin):
            wfjt = factories.v2_workflow_job_template(organization=org)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_workflow_job_template_node(
                    workflow_job_template=wfjt, unified_job_template=jt)

    def test_workflow_admins_can_only_modify_vars_on_nodes_with_permission(self, factories):
        org = factories.v2_organization()
        inv = factories.v2_inventory(organization=org)

        workflow_admin = factories.v2_user()
        org.set_object_roles(workflow_admin, 'Workflow Admin')

        jt = factories.v2_job_template(
            inventory=inv, ask_variables_on_launch=True)
        wfjt = factories.v2_workflow_job_template(organization=org)
        wfnode = factories.v2_workflow_job_template_node(
            workflow_job_template=wfjt, unified_job_template=jt)
        # Verify that the workflow admin can't modify extra vars on templates they don't
        # have access to
        with self.current_user(workflow_admin):
            with pytest.raises(towerkit.exceptions.Forbidden):
                wfnode.extra_data = dict(var1='ansibull')
            assert wfnode.extra_data != dict(var1='ansibull')

        # Grant access to the workflow admin and verify that they can change the extra vars
        jt.set_object_roles(workflow_admin, 'Execute')
        with self.current_user(workflow_admin):
            wfnode.extra_data = dict(var1='parrot')
        assert wfnode.extra_data == dict(var1='parrot')
