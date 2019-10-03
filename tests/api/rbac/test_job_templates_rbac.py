import pytest
import http.client
import json

import awxkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_request,
    check_role_association,
    check_user_capabilities
)
from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class Test_Job_Template_RBAC(APITest):

    def test_unprivileged_user(self, factories):
        """An unprivileged user/team should not be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Launch the JT
        * Edit the JT
        * Delete the JT
        """
        job_template = factories.job_template()
        user = factories.user()

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(job_template, unprivileged=True)

            # check JT launch
            with pytest.raises(awxkit.exceptions.Forbidden):
                job_template.related.launch.post()

            # check put/patch/delete
            assert_response_raised(job_template, http.client.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent):
        """A user/team with JT 'admin' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Edit the JT
        * Delete the JT
        """
        job_template = factories.job_template()
        user = factories.user()

        # give agent admin_role
        set_test_roles(user, job_template, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(job_template, ["credential", "inventory", "project"])

            # check put/patch/delete
            assert_response_raised(job_template.get(), http.client.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_execute_role(self, factories, set_test_roles, agent):
        """A user/team with JT 'execute' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        A user/team with JT 'execute' should not be able to:
        * Edit the JT
        * Delete the JT
        """
        job_template = factories.job_template()
        user = factories.user()

        # give agent execute_role
        set_test_roles(user, job_template, agent, "execute")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(job_template, ["credential", "inventory", "project", "webhook_key"])

            # check put/patch/delete
            assert_response_raised(job_template, http.client.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent):
        """A user/team with JT 'admin' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        A user/team with JT 'admin' should not be able to:
        * Edit the JT
        * Delete the JT
        """
        job_template = factories.job_template()
        user = factories.user()

        # give agent read_role
        set_test_roles(user, job_template, agent, "read")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(job_template, ["credential", "inventory", "project"])

            # check put/patch/delete
            assert_response_raised(job_template, http.client.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_user_capabilities(self, factories, api_job_templates_pg, role):
        """Test user_capabilities given each job_template role."""
        job_template = factories.job_template()
        user = factories.user()

        job_template.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(job_template.get(), role)
            check_user_capabilities(api_job_templates_pg.get(id=job_template.id).results.pop(), role)

    def test_autopopulated_admin_role_with_job_template_creator(self, request, factories, api_job_templates_pg):
        """Verify that job template creators are added to the admin role of the
        created job template.
        """
        # make test user
        org = factories.organization()
        project = factories.project(organization=org)
        inv = factories.project(organization=org)
        cred = factories.credential(organization=org)
        user = factories.user(organization=org)
        # set user resource role associations
        org.set_object_roles(user, 'admin')
        # for resource in (cred, project, inv):
        #    resource.set_object_roles(user, 'use')
        # create a job template as the test user
        with self.current_user(user):
            job_template = factories.job_template(project=project, inventory=inv, credential=cred)
        # verify succesful job_template admin role association
        check_role_association(user, job_template, 'admin')

    @pytest.mark.parametrize('payload_resource_roles, response_codes', [
        (
            {'inventory': ['read'], 'project': ['use']},
            {'PATCH': http.client.FORBIDDEN, 'PUT': http.client.FORBIDDEN}
        ),
        (
            {'inventory': ['use'], 'project': ['read']},
            {'PATCH': http.client.FORBIDDEN, 'PUT': http.client.FORBIDDEN}
        ),
        (
            {'inventory': ['use'], 'project': ['use']},
            {'PATCH': http.client.OK, 'PUT': http.client.OK}
        ),
    ], ids=['only_read_on_inventory', 'only_read_on_project', 'use_access_for_both'])
    def test_job_template_change_request_without_usage_role_returns_code_403(self,
            factories, payload_resource_roles, response_codes):
        """Verify that a user cannot change the related project or inventory
        of a job template unless they have usage permissions to both
        resources and are admins of the job template
        """
        user = factories.user()
        organization = factories.organization()
        cred = factories.credential(organization=organization)
        inv = factories.inventory(organization=organization)
        project = factories.project(organization=organization)
        # so that we change the one resource we don't have access to
        job_template = factories.job_template()
        organization.set_object_roles(user, 'member')
        job_template.set_object_roles(user, 'admin')
        cred.set_object_roles(user, 'use')
        # generate test request payload

        jt_payload = factories.job_template.payload(inventory=inv,
                                                    credential=cred,
                                                    project=project)
        assert jt_payload['project'] == project.id
        assert jt_payload['inventory'] == inv.id
        del jt_payload['credential']
        jt_payload['name'] = job_template.name
        jt_payload['description'] = job_template.description

        # assign test permissions
        for name, roles in payload_resource_roles.items():
            if name == 'inventory':
                inv.set_object_roles(user, *roles)
            elif name == 'project':
                project.set_object_roles(user, *roles)

        # check access
        with self.current_user(username=user.username, password=user.password):
            for method, code in response_codes.items():
                check_request(job_template, method, code, data=jt_payload)

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_launch_job(self, factories, role):
        """Tests ability to launch a job."""
        ALLOWED_ROLES = ['admin', 'execute']
        REJECTED_ROLES = ['read']

        inventory = factories.host().ds.inventory
        job_template = factories.job_template(inventory=inventory)
        user = factories.user()

        job_template.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                job = job_template.launch().wait_until_completed()
                job.assert_successful()
            elif role in REJECTED_ROLES:
                with pytest.raises(awxkit.exceptions.Forbidden):
                    job_template.launch()
            else:
                raise ValueError("Received unhandled job_template role.")

    def test_launch_as_auditor(self, factories):
        """Confirms that a system auditor cannot launch job templates"""
        jt = factories.job_template()
        user = factories.user()
        user.is_system_auditor = True
        with self.current_user(user.username, user.password):
            with pytest.raises(awxkit.exceptions.Forbidden):
                jt.launch().wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_relaunch_job(self, factories, role):
        """Tests ability to relaunch a job."""
        ALLOWED_ROLES = ['admin', 'execute']
        REJECTED_ROLES = ['read']

        inventory = factories.host().ds.inventory
        job_template = factories.job_template(inventory=inventory)
        user = factories.user()

        job_template.set_object_roles(user, role)

        job = job_template.launch().wait_until_completed()
        job.assert_successful()

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                relaunched_job = job.relaunch().wait_until_completed()
                relaunched_job.assert_successful()
            elif role in REJECTED_ROLES:
                with pytest.raises(awxkit.exceptions.Forbidden):
                    job.relaunch()
            else:
                raise ValueError("Received unhandled job_template role.")

    def test_relaunch_with_ask_inventory(self, factories, job_template):
        """Tests relaunch RBAC when ask_inventory_on_launch is true."""
        # FIXME: update for factories when awxkit-210 gets resolved
        job_template.ds.inventory.delete()
        job_template.patch(ask_inventory_on_launch=True)

        credential = job_template.ds.credential
        inventory = factories.host().ds.inventory
        user1, user2 = factories.user(), factories.user()

        # set test permissions
        job_template.set_object_roles(user1, 'execute')
        inventory.set_object_roles(user1, 'use')
        credential.set_object_roles(user1, 'use')
        job_template.set_object_roles(user2, 'execute')

        # launch job as user1
        with self.current_user(username=user1.username, password=user1.password):
            payload = dict(inventory=inventory.id)
            job = job_template.launch(payload).wait_until_completed()

        # relaunch as user2 should raise 403
        with self.current_user(username=user2.username, password=user2.password):
            with pytest.raises(awxkit.exceptions.Forbidden):
                job.relaunch()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_schedule_job(self, factories, role):
        """Tests ability to schedule a job."""
        ALLOWED_ROLES = ['admin', 'execute']
        REJECTED_ROLES = ['read']

        job_template = factories.job_template()
        user = factories.user()

        job_template.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                schedule = job_template.add_schedule()
                assert_response_raised(schedule, methods=('get', 'put', 'patch', 'delete'))
            elif role in REJECTED_ROLES:
                with pytest.raises(awxkit.exceptions.Forbidden):
                    job_template.add_schedule()
            else:
                raise ValueError("Received unhandled job_template role.")

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_cancel_job(self, factories, role):
        """Tests job cancellation. JT admins can cancel other people's jobs."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['execute', 'read']

        inventory = factories.host().ds.inventory
        job_template = factories.job_template(inventory=inventory,
                                              playbook='sleep.yml',
                                              extra_vars=json.dumps(dict(sleep_interval=10)))
        user = factories.user()

        job_template.set_object_roles(user, role)

        # launch job_template
        job = job_template.launch()

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                job.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(awxkit.exceptions.Forbidden):
                    job.cancel()
                # wait for job to finish to ensure clean teardown
                job.wait_until_completed()
            else:
                raise ValueError("Received unhandled job_template role.")

    def test_delete_job_as_org_admin(self, factories):
        """Create two JTs and launch each JT. Verify that each org admin can only
        delete jobs from his own organization.
        """
        # create two JTs from different orgs
        jt1, jt2 = [factories.job_template() for _ in range(2)]
        org1, org2 = [jt.ds.inventory.ds.organization for jt in (jt1, jt2)]
        assert org1.id != org2.id  # sanity check

        # create org_admins
        org_admin1, org_admin2 = [factories.user(organization=org) for org in (org1, org2)]
        org1.add_admin(org_admin1)
        org2.add_admin(org_admin2)

        # launch JTs
        job1, job2 = [jt.launch().wait_until_completed() for jt in (jt1, jt2)]

        # assert that each org_admin cannot delete other organization's job
        with self.current_user(username=org_admin1.username, password=org_admin1.password):
            with pytest.raises(awxkit.exceptions.Forbidden):
                job2.delete()
        with self.current_user(username=org_admin2.username, password=org_admin2.password):
            with pytest.raises(awxkit.exceptions.Forbidden):
                job1.delete()

        # assert that each org_admin can delete his own organization's job
        with self.current_user(username=org_admin1.username, password=org_admin1.password):
            job1.delete()
        with self.current_user(username=org_admin2.username, password=org_admin2.password):
            job2.delete()

    def test_delete_job_as_org_user(self, factories):
        """Tests ability to delete a job as a privileged org_user."""
        inventory = factories.host().ds.inventory
        job_template = factories.job_template(inventory=inventory)
        user = factories.user()

        job_template.set_object_roles(user, 'admin')

        # launch job_template
        job = job_template.launch().wait_until_completed()

        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(awxkit.exceptions.Forbidden):
                job.delete()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_job_user_capabilities(self, factories, api_jobs_pg, role):
        """Test user_capabilities given each JT role on spawned jobs."""
        inventory = factories.host().ds.inventory
        job_template = factories.job_template(inventory=inventory)
        user = factories.user()

        job_template.set_object_roles(user, role)

        # launch job_template
        job = job_template.launch().wait_until_completed()

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(job.get(), role)
            check_user_capabilities(api_jobs_pg.get(id=job.id).results.pop(), role)
