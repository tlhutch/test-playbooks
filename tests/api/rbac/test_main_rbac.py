import pytest

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    check_role_association,
    check_role_disassociation,
    get_resource_roles
)
from tests.api import APITest


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Main_RBAC(APITest):

    @pytest.mark.parametrize('endpoint', ['related_users', 'related_roles'])
    @pytest.mark.parametrize(
        'resource_name',
        ['organization', 'team', 'project', 'inventory', 'inventory_script', 'credential', 'job_template', 'workflow_job_template']
    )
    def test_role_association_and_disassociation(self, factories, resource_name, endpoint):
        """Verify basic role association and disassociation functionality."""
        resource = getattr(factories, resource_name)()
        # make credential and user organization align in testing credentials
        if resource.type == 'credential':
            user = factories.user(organization=resource.ds.organization)
        else:
            user = factories.user()
        for role in resource.object_roles:
            role_name = role.name
            # associate the role with the user
            resource.set_object_roles(user, role_name, endpoint=endpoint)
            check_role_association(user, resource, role_name)
            # disassociate the role from the user
            resource.set_object_roles(user, role_name, endpoint=endpoint, disassociate=True)
            check_role_disassociation(user, resource, role_name)

    @pytest.mark.parametrize(
        'resource_name',
        ['organization', 'team', 'project', 'inventory', 'inventory_script', 'credential', 'job_template', 'workflow_job_template']
    )
    def test_role_association_and_disassociation_as_resource_admin(self, factories, resource_name):
        """Verify that an admin of a resource can grant/revoke other users resource roles."""
        organization = factories.organization()
        admin_user = factories.user(organization=organization)
        user = factories.user(organization=organization)
        if resource_name == 'credential':
            resource = factories.credential(organization=organization)
        else:
            resource = getattr(factories, resource_name)()

        # grant admin_user resource-admin privileges
        resource.set_object_roles(admin_user, "admin")
        if resource_name == 'organization':
            # If associating to organization admin / member, requesting user
            # must be admin of the user's organization too
            # see: https://github.com/ansible/tower/issues/1189
            organization.set_object_roles(admin_user, "admin")

        # verify that our resource admin may grant and revoke all resource roles
        role_names = get_resource_roles(resource)
        with self.current_user(username=admin_user.username, password=admin_user.password):
            for role in role_names:
                resource.set_object_roles(user, role)
                resource.set_object_roles(user, role, disassociate=True)

    @pytest.mark.parametrize(
        'resource_name',
        ['organization', 'team', 'project', 'inventory', 'inventory_script', 'credential', 'job_template', 'workflow_job_template']
    )
    def test_role_association_and_disassociation_as_resource_nonadmin(self, factories, resource_name):
        """Verify that an non-admin of a resource can grant/revoke other users resource roles.
        Here, we give our nonadmin_user all of our resource roles besides the admin role.
        """
        organization = factories.organization()
        nonadmin_user = factories.user(organization=organization)
        user = factories.user(organization=organization)
        if resource_name == 'credential':
            resource = factories.credential(organization=organization)
        else:
            resource = getattr(factories, resource_name)()

        # grant nonadmin_user all resource permissions besides our admin permission
        role_names = get_resource_roles(resource)
        for rn in role_names:
            if rn != "admin":
                resource.set_object_roles(nonadmin_user, rn)

        # verify that our resource nonadmin may not grant all resource roles
        role_names = get_resource_roles(resource)
        with self.current_user(username=nonadmin_user.username, password=nonadmin_user.password):
            for role in role_names:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    resource.set_object_roles(user, role)

        # verify that our resource nonadmin may not revoke all resource roles
        for rn in role_names:
            resource.set_object_roles(user, rn)
        with self.current_user(username=nonadmin_user.username, password=nonadmin_user.password):
            for role in role_names:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    resource.set_object_roles(user, role, disassociate=True)

    @pytest.mark.parametrize('endpoint', ['related_users', 'related_roles'])
    @pytest.mark.parametrize(
        'resource_name, initial_role, unauthorized_target_role',
        [
            ('organization', 'member', 'admin'),
            ('team', 'read', 'admin'),
            ('project', 'read', 'admin'),
            ('inventory', 'read', 'admin'),
            ('inventory_script', 'read', 'admin'),
            ('credential', 'read', 'admin'),
            ('job_template', 'read', 'admin'),
            ('workflow_job_template', 'read', 'admin')
        ]
    )
    def test_unauthorized_self_privilege_escalation_returns_code_403(self, factories, endpoint,
        resource_name, initial_role, unauthorized_target_role):
        """A user with [intial_role] permission on a [resource_name] cannot add
        the [unauthorized_target_role] for the [resource_name] to themselves
        """
        # make credential and user organization align in testing credentials
        if resource_name == 'credential':
            organization = factories.organization()
            user = factories.user(organization=organization)
            resource = getattr(factories, resource_name)(organization=organization)
        else:
            user = factories.user()
            resource = getattr(factories, resource_name)()
        # make a test user and associate it with the initial role
        resource.set_object_roles(user, initial_role)
        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                resource.set_object_roles(user, unauthorized_target_role, endpoint=endpoint)

    @pytest.mark.parametrize(
        'resource',
        ['team', 'project', 'inventory', 'inventory_script', 'credential', 'workflow_job_template', 'notification_template', 'label']
    )
    def test_change_resource_organization_affiliation_with_organization_roles(self, factories, resource):
        """Confirm attempts to change resource organization to an unaffiliated one results in 403 for
        all organization roles.
        """
        org1 = factories.organization()
        org2 = factories.organization()
        resource = getattr(factories, resource)(organization=org1)
        user = factories.user()

        # all organization roles should not allow for resource organization change
        role_names = get_resource_roles(org1)
        for role in role_names:
            org1.set_object_roles(user, role)
            with self.current_user(username=user.username, password=user.password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    resource.organization = org2.id
            org1.set_object_roles(user, role, disassociate=True)

    @pytest.mark.parametrize(
        'resource',
        ['team', 'project', 'inventory', 'inventory_script', 'credential', 'workflow_job_template']
    )
    def test_change_resource_organization_affiliation_with_resource_roles(self, factories, resource):
        """Confirm attempts to change resource organization to an unaffiliated one results in 403 for
        all resource roles.
        """
        org1 = factories.organization()
        org2 = factories.organization()
        resource = getattr(factories, resource)(organization=org1)
        user = factories.user(organization=org1)

        # all organization roles should not allow for resource organization change
        role_names = get_resource_roles(resource)
        for role in role_names:
            resource.set_object_roles(user, role)
            with self.current_user(username=user.username, password=user.password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    resource.organization = org2.id
            resource.set_object_roles(user, role, disassociate=True)

    @pytest.mark.parametrize(
        'resource',
        ['team', 'project', 'inventory', 'inventory_script', 'credential', 'workflow_job_template', 'notification_template', 'label']
    )
    def test_change_resource_organization_affiliation_with_org_admin(self, factories, resource):
        """Confirm attempts to change resource organization to an unaffiliated one results in 403 as
        an organization admin. Our change should succeed however if our user is an admin of both
        oranizations.
        """
        org1 = factories.organization()
        org2 = factories.organization()
        resource = getattr(factories, resource)(organization=org1)
        user = factories.user(organization=org1)
        org1.add_admin(user)

        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                resource.organization = org2.id

        org2.add_admin(user)
        with self.current_user(username=user.username, password=user.password):
            # team organization change is specifically disallowed
            if resource.type == "team":
                with pytest.raises(towerkit.exceptions.Forbidden):
                    resource.organization = org2.id
            else:
                resource.organization = org2.id

    @pytest.mark.parametrize(
        'resource_name, fixture_name',
        [
            ('organization', 'api_organizations_pg'),
            ('team', 'api_teams_pg'),
            ('project', 'api_projects_pg'),
            ('inventory', 'api_inventories_pg'),
            ('inventory_script', 'api_inventory_scripts_pg'),
            ('credential', 'api_credentials_pg'),
            ('job_template', 'api_job_templates_pg'),
            ('workflow_job_template', 'api_workflow_job_templates_pg')
        ], ids=['organization', 'team', 'project', 'inventory',
                'inventory_script', 'credential', 'job_template',
                'workflow_job_template']
    )
    def test_admin_role_filter(self, request, factories, resource_name, fixture_name):
        """Tower supports query filters of the following form: /api/v1/projects/?role_level=admin_role.
        Test that this query filter works with the admin role of select Tower resources. Note: we choose
        not to test other roles here because the admin role filter is the filter used in the UI.
        """
        # create tower resources
        if resource_name == 'credential':
            organization = factories.organization()
            user = factories.user(organization=organization)
            admin_resource = factories.credential(organization=organization)
            factories.credential(organization=organization)
        else:
            user = factories.user()
            admin_resource = getattr(factories, resource_name)()
            getattr(factories, resource_name)()

        admin_resource.set_object_roles(user, 'admin')

        with self.current_user(username=user.username, password=user.password):
            query_results = request.getfixturevalue(request, fixture_name).get(role_level='admin_role')
            # only one of our two resources should get returned
            assert query_results.count == 1, \
                "Unexpected number of query results returned. Expected one, received {0}.".format(query_results.count)
            # assert that our query filter returns the correct resource
            assert query_results.results[0].endpoint == admin_resource.endpoint, \
                "Incorrect Tower resource returned.\n\nExpected: {0}\nReceived {1}.".format(
                    admin_resource.endpoint, query_results.results[0].endpoint)

    @pytest.mark.parametrize('resource_name', ['job_template', 'workflow_job_template'])
    def test_admin_role_filter_polymorphic(self, factories, resource_name, api_unified_job_templates_pg):
        """To a limited extent, tower also supports query filters of the following form:
        /api/v1/unified_job_template/?role_level=admin_role.
        """
        user = factories.user()
        admin_resource = getattr(factories, resource_name)()
        getattr(factories, resource_name)()

        admin_resource.set_object_roles(user, 'admin')

        with self.current_user(user):
            query_results = api_unified_job_templates_pg.get(role_level='admin_role')
            # only one of our two resources should get returned
            assert query_results.count == 1, \
                "Unexpected number of query results returned. Expected one, received {0}.".format(query_results.count)
            # assert that our query filter returns the correct resource
            assert query_results.results[0].endpoint == admin_resource.endpoint, \
                "Incorrect Tower resource returned.\n\nExpected: {0}\nReceived {1}.".format(
                    admin_resource.endpoint, query_results.results[0].endpoint)
