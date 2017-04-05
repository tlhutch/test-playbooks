import pytest
import httplib
import json

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_request,
    check_role_association,
    check_user_capabilities,
    set_roles
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_Job_Template_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        """An unprivileged user/team should not be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Launch the JT
        * Edit the JT
        * Delete the JT
        """
        job_template_pg = factories.job_template()
        user_pg = factories.user()
        launch_pg = job_template_pg.get_related('launch')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(job_template_pg, unprivileged=True)

            # check JT launch
            with pytest.raises(towerkit.exceptions.Forbidden):
                launch_pg.post()

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with JT 'admin' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Edit the JT
        * Delete the JT
        """
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, job_template_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(job_template_pg, ["credential", "inventory", "project"])

            # check put/patch/delete
            assert_response_raised(job_template_pg.get(), httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_execute_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with JT 'execute' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        A user/team with JT 'execute' should not be able to:
        * Edit the JT
        * Delete the JT
        """
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give agent execute_role
        set_test_roles(user_pg, job_template_pg, agent, "execute")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(job_template_pg, ["credential", "inventory", "project"])

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with JT 'admin' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        A user/team with JT 'admin' should not be able to:
        * Edit the JT
        * Delete the JT
        """
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, job_template_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(job_template_pg, ["credential", "inventory", "project"])

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_user_capabilities(self, factories, user_password, api_job_templates_pg, role):
        """Test user_capabilities given each job_template role."""
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(job_template_pg.get(), role)
            check_user_capabilities(api_job_templates_pg.get(id=job_template_pg.id).results.pop(), role)

    def test_autopopulated_admin_role_with_job_template_creator(self, factories, api_job_templates_pg):
        """Verify that job template creators are added to the admin role of the
        created job template.
        """
        # make test user
        user = factories.user()
        # generate job template test payload
        data, resources = factories.job_template.payload()
        # set user resource role associations
        set_roles(user, resources['organization'], ['admin'])
        for name in ('credential', 'project', 'inventory'):
            set_roles(user, resources[name], ['use'])
        # create a job template as the test user
        with self.current_user(username=user.username, password=user.password):
            job_template = api_job_templates_pg.post(data)
        # verify succesful job_template admin role association
        check_role_association(user, job_template, 'admin')

    @pytest.mark.parametrize('payload_resource_roles, response_codes', [
        (
            {'credential': ['read'], 'inventory': ['use'], 'project': ['use']},
            {'PATCH': httplib.FORBIDDEN, 'PUT': httplib.FORBIDDEN}
        ),
        (
            {'credential': ['use'], 'inventory': ['read'], 'project': ['use']},
            {'PATCH': httplib.FORBIDDEN, 'PUT': httplib.FORBIDDEN}
        ),
        (
            {'credential': ['use'], 'inventory': ['use'], 'project': ['read']},
            {'PATCH': httplib.FORBIDDEN, 'PUT': httplib.FORBIDDEN}
        ),
        (
            {'credential': ['use'], 'inventory': ['use'], 'project': ['use']},
            {'PATCH': httplib.OK, 'PUT': httplib.OK}
        ),
    ])
    def test_job_template_change_request_without_usage_role_returns_code_403(self,
            factories, payload_resource_roles, response_codes):
        """Verify that a user cannot change the related project, inventory, or
        credential of a job template unless they have usage permissions on all
        three resources and are admins of the job template
        """
        user = factories.user()
        organization = factories.organization()
        job_template = factories.job_template(organization=organization)
        set_roles(user, organization, ['member'])
        set_roles(user, job_template, ['admin'])
        # generate test request payload
        data, resources = factories.job_template.payload(
            organization=organization)
        # assign test permissions
        for name, roles in payload_resource_roles.iteritems():
            set_roles(user, resources[name], roles)
        # check access
        with self.current_user(username=user.username, password=user.password):
            for method, code in response_codes.iteritems():
                check_request(job_template, method, code, data=data)

    def test_job_template_post_request_without_network_credential_access(self,
            factories, api_job_templates_pg):
        """Verify that job_template post requests with network credentials in
        the payload are only permitted if the user making the request has usage
        permission for the network credential.
        """
        # set user resource role associations
        data, resources = factories.job_template.payload()
        organization = resources['organization']
        user = factories.user(organization=organization)
        for name in ('credential', 'project', 'inventory'):
            set_roles(user, resources[name], ['use'])
        # make network credential and add it to payload
        network_credential = factories.credential(kind='net', organization=organization)
        data['network_credential'] = network_credential.id
        # check POST response code with network credential read permissions
        set_roles(user, network_credential, ['read'])
        with self.current_user(user.username, password=user.password):
            check_request(api_job_templates_pg, 'POST', httplib.FORBIDDEN, data)
        # add network credential usage role permissions to test user
        set_roles(user, network_credential, ['use'])
        # verify that the POST request is now permitted
        with self.current_user(user.username, password=user.password):
            check_request(api_job_templates_pg, 'POST', httplib.CREATED, data)

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_launch_job(self, factories, user_password, role):
        """Tests ability to launch a job."""
        ALLOWED_ROLES = ['admin', 'execute']
        REJECTED_ROLES = ['read']

        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                job_pg = job_template_pg.launch().wait_until_completed()
                assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    job_template_pg.launch()
            else:
                raise ValueError("Received unhandled job_template role.")

    def test_launch_as_auditor(self, factories):
        """Confirms that a system auditor cannot launch job templates"""
        jt = factories.job_template()
        user = factories.user()
        user.is_system_auditor = True
        with self.current_user(user.username, user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                jt.launch().wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_relaunch_job(self, factories, user_password, role):
        """Tests ability to relaunch a job."""
        ALLOWED_ROLES = ['admin', 'execute']
        REJECTED_ROLES = ['read']

        job_template_pg = factories.job_template()
        user_pg = factories.user()
        job_pg = job_template_pg.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                relaunched_job_pg = job_pg.relaunch().wait_until_completed()
                assert relaunched_job_pg.is_successful, "Job unsuccessful - %s." % job_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    job_pg.relaunch()
            else:
                raise ValueError("Received unhandled job_template role.")

    def test_relaunch_with_ask_inventory(self, factories, job_template, user_password):
        """Tests relaunch RBAC when ask_inventory_on_launch is true."""
        # FIXME: update for when factories get fixed for #821
        job_template.get_related('inventory').delete()
        job_template.patch(ask_inventory_on_launch=True)

        credential = job_template.get_related('credential')
        inventory = factories.inventory()
        user1 = factories.user()
        user2 = factories.user()

        # set test permissions
        set_roles(user1, job_template, ['execute'])
        set_roles(user1, inventory, ['use'])
        set_roles(user1, credential, ['use'])
        set_roles(user2, job_template, ['execute'])

        # launch job as user1
        with self.current_user(username=user1.username, password=user_password):
            payload = dict(inventory=inventory.id)
            job_pg = job_template.launch(payload).wait_until_completed()

        # relaunch as user2 should raise 403
        with self.current_user(username=user2.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                job_pg.get_related('relaunch').post()

    def test_relaunch_with_ask_credential(self, factories, job_template_no_credential, user_password):
        """Tests relaunch RBAC when ask_credential_on_launch is true."""
        job_template_no_credential.patch(ask_credential_on_launch=True)

        credential = factories.credential()
        user1 = factories.user(organization=credential.get_related('organization'))
        user2 = factories.user()

        # set test permissions
        set_roles(user1, job_template_no_credential, ['execute'])
        set_roles(user1, credential, ['use'])
        set_roles(user2, job_template_no_credential, ['execute'])

        # launch job as user1
        with self.current_user(username=user1.username, password=user_password):
            payload = dict(credential=credential.id)
            job_pg = job_template_no_credential.launch(payload).wait_until_completed()

        # relaunch as user2 should raise 403
        with self.current_user(username=user2.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                job_pg.get_related('relaunch').post()

    def test_relaunch_job_as_auditor(self, factories, job_with_status_completed):
        """Confirms that a system auditor cannot relaunch a job"""
        user = factories.user()
        user.is_system_auditor = True
        with self.current_user(user.username, user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                job_with_status_completed.relaunch().wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_schedule_job(self, factories, role):
        """Tests ability to schedule a job."""
        ALLOWED_ROLES = ['admin', 'execute']
        REJECTED_ROLES = ['read']

        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        with self.current_user(username=user_pg.username, password=user_pg.password):
            if role in ALLOWED_ROLES:
                schedule_pg = job_template_pg.add_schedule()
                assert_response_raised(schedule_pg, methods=('get', 'put', 'patch', 'delete'))
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    job_template_pg.add_schedule()
            else:
                raise ValueError("Received unhandled job_template role.")

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_cancel_job(self, factories, user_password, role):
        """Tests job cancellation. JT admins can cancel other people's jobs."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['execute', 'read']

        job_template_pg = factories.job_template(playbook='sleep.yml', extra_vars=json.dumps(dict(sleep_interval=10)))
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        # launch job_template
        job_pg = job_template_pg.launch()

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                job_pg.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    job_pg.cancel()
                # wait for job to finish to ensure clean teardown
                job_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled job_template role.")

    def test_delete_job_as_org_admin(self, factories, user_password):
        """Create a run and a scan JT and an org_admin for each of these JTs. Then check
        that each org_admin may only delete his org's job.
        Note: job deletion is organization scoped. A run JT's project determines its
        organization and a scan JT's inventory determines its organization.
        """
        # create two JTs
        run_job_template = factories.job_template()
        scan_job_template = factories.job_template(job_type="scan", project=None)

        # sanity check
        run_jt_org = run_job_template.get_related('project').get_related('organization')
        scan_jt_org = scan_job_template.get_related('inventory').get_related('organization')
        assert run_jt_org.id != scan_jt_org.id, "Test JTs unexpectedly in the same organization."

        # create org_admins
        org_admin1 = factories.user(organization=run_jt_org)
        org_admin2 = factories.user(organization=scan_jt_org)
        set_roles(org_admin1, run_jt_org, ['admin'])
        set_roles(org_admin2, scan_jt_org, ['admin'])

        # launch JTs
        run_job = run_job_template.launch()
        scan_job = scan_job_template.launch()

        # assert that each org_admin cannot delete other organization's job
        with self.current_user(username=org_admin1.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                scan_job.delete()
        with self.current_user(username=org_admin2.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                run_job.delete()

        # assert that each org_admin can delete his own organization's job
        with self.current_user(username=org_admin1.username, password=user_password):
            run_job.delete()
        with self.current_user(username=org_admin2.username, password=user_password):
            scan_job.delete()

    def test_delete_job_as_org_user(self, factories, user_password):
        """Tests ability to delete a job as a privileged org_user."""
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, ['admin'])

        # launch job_template
        job_pg = job_template_pg.launch()

        with self.current_user(username=user_pg.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                job_pg.delete()
            # wait for project to finish to ensure clean teardown
            job_pg.wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_job_user_capabilities(self, factories, user_password, api_jobs_pg, role):
        """Test user_capabilities given each JT role on spawned jobs."""
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        # launch job_template
        job_pg = job_template_pg.launch().wait_until_completed()

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(job_pg.get(), role)
            check_user_capabilities(api_jobs_pg.get(id=job_pg.id).results.pop(), role)
