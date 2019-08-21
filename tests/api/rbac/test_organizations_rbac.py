from collections import namedtuple

import pytest
import http.client

import awxkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_user_capabilities
)
from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class Test_Organization_RBAC(APITest):

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

    SubResourceMapping = namedtuple('SubResourceMapping', [
        'resource_type', 'field', 'sub_resource'])

    sub_resource_mappings = [
        SubResourceMapping(resource_type='ad_hoc_command', field='credential',
                           sub_resource=('credential', {})),
        SubResourceMapping(resource_type='ad_hoc_command', field='inventory',
                           sub_resource=('inventory', {})),
        SubResourceMapping(resource_type='group', field='inventory',
                           sub_resource=('inventory', {})),
        SubResourceMapping(resource_type='host', field='inventory',
                           sub_resource=('inventory', {})),
        SubResourceMapping(resource_type='inventory', field='insights_credential',
                           sub_resource=('credential', dict(kind='insights'))),
        SubResourceMapping(resource_type='inventory_source', field='credential',
                           sub_resource=('credential', dict(kind='aws'))),
        SubResourceMapping(resource_type='inventory_source', field='project',
                           sub_resource=('project', {})),
        SubResourceMapping(resource_type='job_template', field='credential',
                           sub_resource=('credential', dict(kind='ssh'))),
        SubResourceMapping(resource_type='job_template', field='inventory',
                           sub_resource=('inventory', {})),
        SubResourceMapping(resource_type='job_template', field='project',
                           sub_resource=('project', {})),
        SubResourceMapping(resource_type='job_template', field='vault_credential',
                           sub_resource=('credential', dict(kind='vault', inputs=dict(vault_password='foo')))),
        SubResourceMapping(resource_type='project', field='credential',
                           sub_resource=('credential', dict(kind='scm'))),
        SubResourceMapping(resource_type='workflow_job_template_node', field='credentials',
                           sub_resource=('credential', dict(kind='ssh'))),
        SubResourceMapping(resource_type='workflow_job_template_node', field='inventory',
                           sub_resource=('inventory', {})),
        SubResourceMapping(resource_type='workflow_job_template_node', field='unified_job_template',
                           sub_resource=('job_template', {})),
        SubResourceMapping(resource_type='workflow_job_template_node', field='workflow_job_template',
                           sub_resource=('workflow_job_template', {})),
    ]

    org_resource_admin_sub_resource_mappings = []
    for i in org_resource_admin_mappings:
        for j in sub_resource_mappings:
            if i.resource_type == j.resource_type:
                org_resource_admin_sub_resource_mappings.append((i, j))

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
            assert_response_raised(organization, http.client.FORBIDDEN)

    @pytest.mark.yolo
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
            assert_response_raised(organization, http.client.FORBIDDEN)

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
            assert_response_raised(organization, http.client.OK)

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
            assert_response_raised(organization, http.client.FORBIDDEN)

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
            assert_response_raised(organization, http.client.FORBIDDEN)

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
            with pytest.raises(awxkit.exceptions.Forbidden):
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
            with pytest.raises(awxkit.exceptions.Forbidden):
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
            with pytest.raises(awxkit.exceptions.Forbidden):
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
        inv_source1 = factories.inventory_source(inventory=inv1, source_script=inv_script1)
        inv_source2 = factories.inventory_source(inventory=inv2, source_script=inv_script2)

        inv_update1 = inv_source1.update().wait_until_completed()
        inv_update2 = inv_source2.update().wait_until_completed()

        with self.current_user(username=org_admin.username, password=org_admin.password):
            inv_update1.delete()
            with pytest.raises(awxkit.exceptions.Forbidden):
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

        with pytest.raises(awxkit.exceptions.BadRequest):
            organization.set_object_roles(team, role)

    @staticmethod
    def create_resource(factories, res_type, org, **kwargs_input):
        kwargs = kwargs_input.copy()
        m2m_cred = None
        if 'credentials' in kwargs:
            m2m_cred = kwargs.pop('credentials')
        if res_type == 'inventory_source':
            kwargs['source_script'] = factories.inventory_script(organization=org)
        if res_type == 'job_template':
            # Would like to specify kwargs like 'project': (Project, {Organization: org})
            # but something about the awxkit dependency store does not work for that
            if not kwargs.get('project'):
                kwargs['project'] = factories.project(organization=org)
            if not kwargs.get('inventory'):
                kwargs['inventory'] = factories.inventory(organization=org)
            if not kwargs.get('credential'):
                kwargs['credential'] = factories.credential(organization=org)
        else:
            kwargs['organization'] = org
        obj = getattr(factories, res_type)(**kwargs)
        if m2m_cred:
            obj.add_credential(m2m_cred)
        return obj

    @pytest.mark.parametrize('resource_type', [item.resource_type for item in org_resource_admin_mappings])
    def test_non_authorized_user_cannot_create_resources(self, factories, resource_type, non_superuser):
        org = factories.organization()
        with self.current_user(non_superuser):
            with pytest.raises(awxkit.exceptions.Forbidden):
                self.create_resource(factories, resource_type, org)

    @pytest.mark.parametrize('resource_type', [item.resource_type for item in org_resource_admin_mappings])
    def test_org_admin_can_create_resources(self, factories, resource_type):
        org = factories.organization()
        org_admin = factories.user()
        org.add_admin(org_admin)
        with self.current_user(org_admin):
            self.create_resource(factories, resource_type, org)

    @pytest.mark.parametrize('sub_resource_mapping', sub_resource_mappings,
                            ids=lambda x: '{}.{}'.format(x.resource_type, x.field))
    def test_org_admin_create_resources_with_sub_resource(self, factories, sub_resource_mapping):
        orgA, orgB = [factories.organization() for _ in range(2)]
        sub_resource = self.create_resource(factories, sub_resource_mapping.sub_resource[0], orgA,
                                            **sub_resource_mapping.sub_resource[1])
        user = factories.user()
        orgB.add_admin(user)
        if sub_resource_mapping.field == 'vault_credential':
            creation_kwargs = {sub_resource_mapping.field: sub_resource.id}
        else:
            creation_kwargs = {sub_resource_mapping.field: sub_resource}
        if sub_resource_mapping.resource_type == 'workflow_job_template_node':
            if sub_resource_mapping.field != 'workflow_job_template':
                creation_kwargs['workflow_job_template'] = factories.workflow_job_template(organization=orgB)
            if sub_resource_mapping.field == 'inventory':
                creation_kwargs['unified_job_template'] = self.create_resource(factories, 'job_template', orgB,
                                                                               ask_inventory_on_launch=True)
            if sub_resource_mapping.field == 'credentials':
                creation_kwargs['unified_job_template'] = self.create_resource(factories, 'job_template', orgB,
                                                                               ask_credential_on_launch=True)
        if sub_resource_mapping.resource_type == 'inventory_source':
            if sub_resource_mapping.field != 'inventory':
                creation_kwargs['inventory'] = factories.inventory(organization=orgB)
            if sub_resource_mapping.field == 'project':
                creation_kwargs['source'] = 'scm'
            if sub_resource_mapping.field == 'credential':
                creation_kwargs['source_script'] = factories.inventory_script(organization=orgB)
        with self.current_user(user):
            with pytest.raises(awxkit.exceptions.Forbidden):
                self.create_resource(factories, sub_resource_mapping.resource_type, orgB, **creation_kwargs)
        orgA.add_admin(user)
        with self.current_user(user):
            self.create_resource(factories, sub_resource_mapping.resource_type, orgB, **creation_kwargs)

    @pytest.mark.parametrize('role_sub_resource_mapping', org_resource_admin_sub_resource_mappings,
                             ids=lambda x: '{}-{}.{}'.format(x[0].resource_role, x[1].resource_type, x[1].field))
    def test_organization_resource_admins_create_resources_with_sub_resource(self, factories, role_sub_resource_mapping):
        resource_mapping, sub_resource_mapping = role_sub_resource_mapping
        orgA, orgB = [factories.organization() for _ in range(2)]
        sub_resource = self.create_resource(factories, sub_resource_mapping.sub_resource[0], orgA,
                                            **sub_resource_mapping.sub_resource[1])
        user = factories.user()
        if resource_mapping.resource_role == 'Job Template Admin':
            orgB.set_object_roles(user, 'Inventory Admin')
            orgB.set_object_roles(user, 'Project Admin')
            orgB.set_object_roles(user, 'Credential Admin')
        else:
            orgB.set_object_roles(user, resource_mapping.resource_role)
        if sub_resource_mapping.field == 'vault_credential':
            creation_kwargs = {sub_resource_mapping.field: sub_resource.id}
        else:
            creation_kwargs = {sub_resource_mapping.field: sub_resource}
        with self.current_user(user):
            with pytest.raises(awxkit.exceptions.Forbidden):
                self.create_resource(factories, sub_resource_mapping.resource_type, orgB, **creation_kwargs)
        orgA.add_admin(user)
        with self.current_user(user):
            self.create_resource(factories, sub_resource_mapping.resource_type, orgB, **creation_kwargs)

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
            assert_response_raised(resource, http.client.OK)

    @pytest.mark.parametrize('resource_mapping',
                             [m for m in org_resource_admin_mappings
                              if m.resource_type != 'notification_template'],
                             ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_organization_resource_admins_can_grant_permissions_to_internal_users(self, factories, resource_mapping, agent, set_test_roles):
        org = factories.organization()
        resource_admin, user = [factories.user(
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
        resource_admin, user = [factories.user(
            organization=o) for o in (None, None)]
        set_test_roles(resource_admin, org, agent, resource_mapping.resource_role)

        resource = self.create_resource(factories, resource_mapping.resource_type, org)

        with self.current_user(resource_admin):
            if resource_mapping.resource_type == 'credential':
                # Credentials use a different exception
                with pytest.raises(awxkit.exceptions.BadRequest):
                    resource.set_object_roles(user, 'admin')
            else:
                with pytest.raises(awxkit.exceptions.Forbidden):
                    resource.set_object_roles(user, 'admin')

    @pytest.mark.parametrize('resource_mapping', org_resource_admin_mappings, ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_organization_resource_admins_cannot_modify_resources_in_other_orgs(self, factories, resource_mapping, agent, set_test_roles):
        org1, org2 = [factories.organization() for _ in range(2)]
        resource_admin, user = [factories.user(
            organization=o) for o in (None, org2)]

        set_test_roles(resource_admin, org1, agent, resource_mapping.resource_role)

        resource = self.create_resource(factories, resource_mapping.resource_type, org2)

        with self.current_user(resource_admin):
            if resource_mapping.resource_type != 'notification_template':
                # Skip notification_templates because they do not have object-level permissions
                with pytest.raises(awxkit.exceptions.Forbidden):
                    resource.set_object_roles(user, 'admin')
            assert_response_raised(resource, http.client.FORBIDDEN)

    @pytest.mark.parametrize('resource_mapping',
                             org_resource_admin_mappings,
                             ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_resource_permissions_are_deescalated_after_disassociating(self, factories, resource_mapping, agent, set_test_roles):
        """Grant a user resource admin rights, create a resource, remove user's role, and verify
        that they are not able to modify the resource"""
        org = factories.organization()
        resource_admin, user = [factories.user(
            organization=org) for _ in range(2)]
        team = set_test_roles(resource_admin, org, agent, resource_mapping.resource_role)

        resource = self.create_resource(factories, resource_mapping.resource_type, org)

        set_test_roles(resource_admin, org, agent, resource_mapping.resource_role, team=team, disassociate=True)
        with self.current_user(resource_admin):
            if resource_mapping.resource_type != 'notification_template':
                # Skip notification_templates because they do not have object-level permissions
                with pytest.raises(awxkit.exceptions.Forbidden):
                    resource.set_object_roles(user, 'admin')
            assert_response_raised(resource, http.client.FORBIDDEN)

    def test_workflow_admins_cannot_add_templates_to_workflows_without_permission(self, factories):
        org = factories.organization()
        workflow_admin = factories.user()
        org.set_object_roles(workflow_admin, 'Workflow Admin')

        inv = factories.inventory(organization=org)
        jt = factories.job_template(inventory=inv)

        with self.current_user(workflow_admin):
            wfjt = factories.workflow_job_template(organization=org)
            with pytest.raises(awxkit.exceptions.Forbidden):
                factories.workflow_job_template_node(
                    workflow_job_template=wfjt, unified_job_template=jt)

    def test_workflow_admins_can_only_modify_vars_on_nodes_with_permission(self, factories):
        org = factories.organization()
        inv = factories.inventory(organization=org)

        workflow_admin = factories.user()
        org.set_object_roles(workflow_admin, 'Workflow Admin')

        jt = factories.job_template(
            inventory=inv, ask_variables_on_launch=True)
        wfjt = factories.workflow_job_template(organization=org)
        wfnode = factories.workflow_job_template_node(
            workflow_job_template=wfjt, unified_job_template=jt)
        # Verify that the workflow admin can't modify extra vars on templates they don't
        # have access to
        with self.current_user(workflow_admin):
            with pytest.raises(awxkit.exceptions.Forbidden):
                wfnode.extra_data = dict(var1='ansibull')
            assert wfnode.extra_data != dict(var1='ansibull')

        # Grant access to the workflow admin and verify that they can change the extra vars
        jt.set_object_roles(workflow_admin, 'Execute')
        with self.current_user(workflow_admin):
            wfnode.extra_data = dict(var1='parrot')
        assert wfnode.extra_data == dict(var1='parrot')

    @pytest.mark.parametrize('resource_mapping', org_resource_admin_mappings, ids=mapping_id)
    def test_normal_users_cannot_grant_roles(self, factories, resource_mapping):
        org = factories.organization()
        user1, user2 = [factories.user(organization=o) for o in (org, org)]
        with self.current_user(user1):
            with pytest.raises(awxkit.exceptions.Forbidden):
                org.set_object_roles(user2, resource_mapping.resource_role)

    @pytest.mark.parametrize('resource_mapping',
                             [m for m in org_resource_admin_mappings
                             if m.resource_type in ['credential', 'workflow_job_template']],
                             ids=mapping_id)
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_resource_admins_cannot_manage_unassociated_resources(self, factories, resource_mapping, agent, set_test_roles):
        resource = self.create_resource(factories, resource_mapping.resource_type, None)
        resource.organization = None
        org = factories.organization()
        resource_admin, user = [factories.user(
            organization=o) for o in (org, None)]
        set_test_roles(resource_admin, org, agent, resource_mapping.resource_role)
        with self.current_user(resource_admin):
            with pytest.raises(awxkit.exceptions.Forbidden):
                resource.set_object_roles(user, 'admin')


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken')
class TestManageOrgAuthFalse(APITest):

    @pytest.mark.parametrize('endpoint', ['related_users', 'related_roles'])
    def test_org_admins_can_add_resource_admins(self, v2, factories, update_setting_pg, endpoint):
        """Test that users can still be admins of resources when MANAGE_ORGANIZATION_AUTH is set to false.

        Regression test for https://github.com/ansible/tower/issues/3394
        """
        auth_settings = v2.settings.get().get_endpoint('authentication')
        update_setting_pg(auth_settings, dict(MANAGE_ORGANIZATION_AUTH=False))
        org = factories.organization()
        team = factories.team(organization=org)
        proj = factories.project(organization=org)
        jt = factories.job_template(project=proj)
        org_user = factories.user()
        org_user2 = factories.user()
        org_admin = factories.user()

        org.set_object_roles(org_user, "member")
        org.set_object_roles(org_user2, "member")
        team.set_object_roles(org_user, "member")
        org.set_object_roles(org_admin, "admin")

        with self.current_user(org_admin):
            jt.set_object_roles(team, "admin", endpoint=endpoint)

        with self.current_user(org_user):
            jt.set_object_roles(org_user2, "execute", endpoint='related_roles')

        with self.current_user(org_user2):
            jt.launch().wait_until_completed().assert_successful()
