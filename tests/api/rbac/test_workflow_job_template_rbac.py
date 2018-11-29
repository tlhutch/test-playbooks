import pytest
import logging

from tests.lib.helpers.rbac_utils import check_user_capabilities
from tests.api import APITest

from towerkit.exceptions import Forbidden

log = logging.getLogger(__name__)


# WFJ
# - superuser - read, execute, modify
# - auditor - read
# - user / team assigned to role, confirm role access
# WFJT nodes
# WFJ nodes
# WFJT node UJTs
# WFJ node UJs
# Relaunch
# Copying
# Notifications
# All - access to related endpoints

# In each test:
# - access list
# - user capability fields

@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Workflow_Job_Template_RBAC(APITest):

    @pytest.mark.parametrize('wfjt_state', ['wfjt_has_org', 'wfjt_org_null'])
    def test_system_admin_access(self, factories, wfjt_state):
        """A superuser should be able to perform all actions with WFJTs, including:
        - POST new WFJT
        - GET, PUT, PATCH, or DELETE existing WFJTs

        (This is true whether or not a WFJT has been assigned to an organization)
        """
        wfjt = factories.workflow_job_template()
        if wfjt_state == 'wfjt_has_org':
            org = factories.organization()
            wfjt.patch(organization=org.id)
        wfjt.get()
        wfjt.patch()
        wfjt.put()
        wfjt.delete()

    @pytest.mark.parametrize('wfjt_state', ['wfjt_has_org', 'wfjt_org_null'])
    def test_system_auditor_access(self, factories, api_workflow_job_templates_pg, wfjt_state):
        """A system auditor should be able to:
        - GET WFJTs

        A system auditor should not be able to:
        - POST a new WFJT
        - PUT, PATCH or DELETE existing WFJTs

        (This is true whether or not a WFJT has been assigned to an organization)
        """
        sys_auditor = factories.user(is_system_auditor=True)

        # Create WFJT
        wfjt = factories.workflow_job_template()
        if wfjt_state == 'wfjt_has_org':
            org = factories.organization()
            wfjt.patch(organization=org.id)

        # Test access
        with self.current_user(sys_auditor.username, sys_auditor.password):
            with pytest.raises(Forbidden):
                api_workflow_job_templates_pg.post()
            wfjt.get()
            with pytest.raises(Forbidden):
                wfjt.patch()
            with pytest.raises(Forbidden):
                wfjt.put()
            with pytest.raises(Forbidden):
                wfjt.delete()

    def test_org_admin_access(self, factories, api_organizations_pg):
        """An org admin should be able to perform all actions on WFJTs assigned to
        the same organization, including:
        - POST new WFJT
        - GET, PUT, PATCH, or DELETE existing WFJTs
        """
        # Create org admin
        org = factories.organization()
        org_admin = factories.user(organization=org)
        org.add_admin(org_admin)

        # Test access
        with self.current_user(org_admin.username, org_admin.password):
            wfjt = factories.workflow_job_template(organization=org)
            assert wfjt.organization == org.id, \
                "Expected WFJT to be assigned to org '{0}'. Org set to '{1}' instead"\
                .format(org.id, wfjt.organization)
            wfjt.get()
            wfjt.patch()
            wfjt.put()
            wfjt.delete()

    def test_org_auditor_access(self, factories, api_workflow_job_templates_pg, api_organizations_pg):
        """An org auditor should be able to GET existing WFJTs assigned to
        the same organization.

        An org auditor should not be able to:
        - POST new WFJT
        - PUT, PATCH, or DELETE existing WFJTs
        """
        # Create org auditor
        org = factories.organization()
        org_auditor = factories.user(organization=org)
        org.set_object_roles(org_auditor, 'Auditor')

        wfjt = factories.workflow_job_template(organization=org)

        # Test access
        with self.current_user(org_auditor.username, org_auditor.password):
            wfjt.get()
            with pytest.raises(Forbidden):
                api_workflow_job_templates_pg.post()
            with pytest.raises(Forbidden):
                wfjt.patch()
            with pytest.raises(Forbidden):
                wfjt.put()
            with pytest.raises(Forbidden):
                wfjt.delete()

    @pytest.mark.parametrize('role_name', ['Read', 'Execute', 'Admin'])
    def test_regular_user_access(self, factories, api_workflow_job_templates_pg, api_organizations_pg, role_name):
        """An org user with Read access is able to GET a WFJT,
        but not able to POST, PUT, PATCH, or DELETE.

        An org user with Execute access is able to GET a WFJT,
        but not able to POST, PUT, PATCH, or DELETE.

        An org user with Admin access is able to
        GET, POST, PUT, PATCH, and DELETE a WFJT.
        """
        # Create user
        org = factories.organization()
        user = factories.user(organization=org)
        assert len(org.related.users.get(id=user.id).results), \
            "Failed to add user '{0}' to organization '{1}'".format(user.id, org.id)

        # Create WFJT
        wfjt = factories.workflow_job_template(organization=org)

        # Assign role
        wfjt.set_object_roles(user, role_name)

        # Test access
        with self.current_user(user.username, user.password):
            wfjt.get()
            with pytest.raises(Forbidden):
                api_workflow_job_templates_pg.post()
            if role_name == 'Admin':
                wfjt.patch()
                wfjt.put()
                wfjt.delete()
            else:
                with pytest.raises(Forbidden):
                    wfjt.patch()
                with pytest.raises(Forbidden):
                    wfjt.put()
                with pytest.raises(Forbidden):
                    wfjt.delete()

    @pytest.mark.parametrize('role', ['org_admin', 'org_auditor', 'wfjt_read', 'wfjt_execute', 'wfjt_admin'])
    def test_non_org_member_access(self, factories, api_organizations_pg, role):
        """Users should not be able to perform any operations on WFJTs in
        organizations to which they do not belong.
        """
        # Create user
        org = factories.organization()
        user = factories.user()

        # Create WFJT in user's organization
        wfjt = factories.workflow_job_template(organization=org)

        # Create WFJT in other organization
        other_org = factories.organization()
        other_wfjt = factories.workflow_job_template(organization=other_org)

        # Assign role
        if role == 'org_admin':
            org.add_admin(user)
        elif role == 'org_auditor':
            org.set_object_roles(user, 'Auditor')
        elif 'wfjt' in role:
            wfjt_role = role[5:]
            wfjt.set_object_roles(user, wfjt_role)

        # Test access
        with self.current_user(user.username, user.password):
            with pytest.raises(Forbidden):
                factories.workflow_job_template()  # no organization
            with pytest.raises(Forbidden):
                factories.workflow_job_template(organization=other_org)
            with pytest.raises(Forbidden):
                other_wfjt.get()
            with pytest.raises(Forbidden):
                other_wfjt.patch()
            with pytest.raises(Forbidden):
                other_wfjt.put()
            with pytest.raises(Forbidden):
                other_wfjt.delete()

    @pytest.mark.parametrize('source', (
        'workflow',  # tests use role needed for applying inventory to WFJT
        'prompt',    # tests use role needed for launching
    ))
    def test_prompts_access(self, factories, source):
        inventory = factories.inventory()
        if source == 'prompt':
            wfjt = factories.workflow_job_template(ask_inventory_on_launch=True)
        else:
            wfjt = factories.workflow_job_template()

        # set permission to WFJT and inventory
        user = factories.user()
        wfjt.set_object_roles(user, 'Admin')
        inventory.set_object_roles(user, 'Read')  # not sufficient

        with self.current_user(user.username, user.password):
            with pytest.raises(Forbidden):
                if source == 'prompt':
                    wfjt.launch(payload={'inventory': inventory.id})
                else:
                    wfjt.inventory = inventory.id

    def test_user_with_execute_can_use_wfjt_with_inventory(self, factories):
        inventory = factories.inventory()
        wfjt = factories.workflow_job_template(inventory=inventory)

        # assert that if the inventory is allready set,
        # the user with execute permission on the wfjt can launch it
        # Add a node so there is a job to apply the inventory to
        jt = factories.job_template(ask_inventory_on_launch=True)
        factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=jt,
        )
        user = factories.user()
        wfjt.set_object_roles(user, 'Execute')
        jt.set_object_roles(user, 'Read')
        # if the inventory is set in advance by an admin, read permissions on
        # the inventory should be sufficient
        inventory.set_object_roles(user, 'Read')
        with self.current_user(user.username, user.password):
            wfj = wfjt.launch()
            node = wfj.get_related('workflow_nodes').results.pop()
            node.wait_for_job()
            job = node.get_related('job')
            assert job.inventory == inventory.id
            wfj.wait_until_completed()
            assert wfj.status == 'successful'

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_user_capabilities(self, factories, api_workflow_job_templates_pg, role):
        """Test user_capabilities given each WFJT role."""
        wfjt = factories.workflow_job_template()
        user = factories.user()

        # give test user target role privileges
        wfjt.set_object_roles(user, role)

        with self.current_user(user.username, user.password):
            check_user_capabilities(wfjt.get(), role)
            check_user_capabilities(api_workflow_job_templates_pg.get(id=wfjt.id).results.pop(), role)
