# -*- coding: utf-8 -*-
import logging
import types
import json
import re

import towerkit.tower.inventory
import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def job_sleep(request, job_template_sleep):
    """Launch the job_template_sleep and return a job resource."""
    return job_template_sleep.launch()


@pytest.fixture(scope="function")
def job_with_status_pending(job_template_sleep, pause_awx_task_system):
    """Wait for job_sleep to move from new to queued, and return the job."""
    return job_template_sleep.launch().wait_until_started()


@pytest.fixture(scope="function")
def job_with_status_running(request, job_sleep):
    """Wait for job_sleep to move from queued to running, and return the job."""
    return job_sleep.wait_until_status('running')


@pytest.fixture(scope="function")
def job_with_multi_ask_credential_and_password_in_payload(request, job_template_multi_ask, testsetup):
    """Launch job_template_multi_ask with passwords in the payload."""
    launch_pg = job_template_multi_ask.get_related("launch")

    # determine whether sudo or su was used
    credential = job_template_multi_ask.get_related('credential')

    # assert expected values in launch_pg.passwords_needed_to_start
    assert credential.expected_passwords_needed_to_start == launch_pg.passwords_needed_to_start

    # build launch payload
    payload = dict(ssh_password=testsetup.credentials['ssh']['password'],
                   ssh_key_unlock=testsetup.credentials['ssh']['encrypted']['ssh_key_unlock'],
                   become_password=testsetup.credentials['ssh']['become_password'])

    # launch job_template
    result = launch_pg.post(payload)

    # find and return specific job_pg
    jobs_pg = job_template_multi_ask.get_related('jobs', id=result.json['job'])
    assert jobs_pg.count == 1, "Unexpected number of jobs returned (%s != 1)" % jobs_pg.count
    return jobs_pg.results[0]


@pytest.fixture(scope="function", params=['project', 'inventory', 'credential'])
def job_with_deleted_related(request, job_with_status_completed):
    """Creates and deletes an related attribute of a job"""
    related_pg = job_with_status_completed.get_related(request.param)
    related_pg.delete()
    return job_with_status_completed


@pytest.fixture()
def utf8_template(request, authtoken, api_job_templates_pg, project_ansible_playbooks_git, host_local, ssh_credential):
    payload = dict(name="playbook:utf-8.yml.yml, random:%s" % (fauxfactory.gen_utf8()),
                   description="utf-8.yml - %s" % (fauxfactory.gen_utf8()),
                   inventory=host_local.inventory,
                   job_type='run',
                   project=project_ansible_playbooks_git.id,
                   credential=ssh_credential.id,
                   playbook=u'utf-8-䉪ቒ칸ⱷꯔ噂폄蔆㪗輥.yml',)
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def project_with_scm_update_on_launch(request, project_ansible_playbooks_git):
    return project_ansible_playbooks_git.patch(scm_update_on_launch=True)


@pytest.fixture(scope="function")
def job_template_with_cloud_credential(request, job_template, cloud_credential):
    job_template.patch(cloud_credential=cloud_credential.id)
    return job_template


@pytest.fixture(scope="function")
def job_template_with_network_credential(request, job_template, network_credential):
    job_template.patch(network_credential=network_credential.id)
    return job_template


@pytest.fixture(scope="function")
def expected_net_env_vars(testsetup):
    """Returns a list of our expected network job env variables."""
    def func(network_credential):
        expected_env_vars = dict()
        if getattr(network_credential, "username", None):
            expected_env_vars["ANSIBLE_NET_USERNAME"] = testsetup.credentials['network']['username']
        if getattr(network_credential, "password", None):
            expected_env_vars["ANSIBLE_NET_PASSWORD"] = u"**********"
        if getattr(network_credential, "ssh_key_data", None):
            expected_env_vars["ANSIBLE_NET_SSH_KEYFILE"] = u"**********"
        if getattr(network_credential, "authorize", None):
            expected_env_vars["ANSIBLE_NET_AUTHORIZE"] = "1"
        else:
            expected_env_vars["ANSIBLE_NET_AUTHORIZE"] = "0"
        if getattr(network_credential, "authorize_password", None):
            expected_env_vars["ANSIBLE_NET_AUTH_PASS"] = u"**********"
        return expected_env_vars
    return func


def confirm_job_env(job_pg, expected_env_vars):
    """Convenience function to assess that the correct job environment variables
    are present and have the correct values.
    """
    for env_var, env_val in expected_env_vars.items():
        assert env_var in job_pg.job_env, "Missing expected environment variable %s in job_env.\n%s" % \
            (env_var, json.dumps(job_pg.job_env, indent=2))

        if isinstance(env_val, types.FunctionType):
            is_correct = env_val(job_pg.job_env[env_var])
        else:
            is_correct = job_pg.job_env[env_var] == env_val
        assert is_correct, "Unexpected value for environment variable %s in job_env ('%s')." % \
            (env_var, job_pg.job_env[env_var])


def confirm_fact_modules_present(facts, **kwargs):
    """Convenience function to assess fact module contents."""
    assert len(facts) == len(kwargs), "Unexpected number of new facts found ..."
    module_names = [x.module for x in facts]
    for (mod_name, mod_count) in kwargs.items():
        assert module_names.count(mod_name) == mod_count, "Unexpected number of facts found (%d) for module %s" % (mod_count, mod_name)


def azure_type(azure_credential):
    """Convenience function that returns our type of new-style Azure credential"""
    azure_attrs = ['subscription', 'tenant', 'secret', 'client']
    azure_ad_attrs = ['subscription', 'username', 'password']
    if all([getattr(azure_credential, attr, None) for attr in azure_attrs]):
        return 'azure'
    elif all([getattr(azure_credential, attr, None) for attr in azure_ad_attrs]):
        return 'azure_ad'
    else:
        raise ValueError("Unhandled credential received - %s." % azure_credential)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.ansible_integration
    def test_utf8(self, utf8_template):
        """Verify that a playbook full of UTF-8 successfully works through Tower"""
        # launch job
        job_pg = utf8_template.launch_job()

        # wait for completion
        job_pg = job_pg.wait_until_completed(timeout=60 * 10)

        # assert successful completion of job
        assert job_pg.is_successful, "Job unsuccessful - %s " % job_pg

    def test_post_as_superuser(self, job_template, api_jobs_pg):
        """Verify a superuser is able to create a job by POSTing to the /api/v1/jobs endpoint."""
        # post a job
        job_pg = api_jobs_pg.post(job_template.json)

        # assert successful post
        assert job_pg.status == 'new'

    def test_post_as_non_superuser(self, non_superusers, user_password, api_jobs_pg, job_template):
        """Verify a non-superuser is unable to create a job by POSTing to the /api/v1/jobs endpoint."""
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    api_jobs_pg.post(job_template.json)

    def test_relaunch_with_credential(self, job_with_status_completed):
        """Verify relaunching a job with a valid credential no-ask credential."""
        relaunch_pg = job_with_status_completed.get_related('relaunch')

        # assert values on relaunch resource
        assert not relaunch_pg.passwords_needed_to_start

        # relaunch the job and wait for completion
        job_pg = job_with_status_completed.relaunch().wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_relaunch_with_deleted_related(self, job_with_deleted_related):
        """Verify relaunching a job whose related information has been deleted."""
        # get relaunch page
        relaunch_pg = job_with_deleted_related.get_related('relaunch')

        # assert values on relaunch resource
        assert not relaunch_pg.passwords_needed_to_start

        # attempt to relaunch the job, should raise exception
        with pytest.raises(towerkit.exceptions.BadRequest):
            relaunch_pg.post()

    def test_relaunch_with_multi_ask_credential_and_passwords_in_payload(self, job_with_multi_ask_credential_and_password_in_payload, testsetup):  # NOQA
        """Verify that relaunching a job with a credential that includes ASK passwords, behaves as expected when
        supplying the necessary passwords in the relaunch payload.
        """
        # get relaunch page
        relaunch_pg = job_with_multi_ask_credential_and_password_in_payload.get_related('relaunch')

        # determine expected passwords
        credential = job_with_multi_ask_credential_and_password_in_payload.get_related('credential')

        # assert expected values in relaunch_pg.passwords_needed_to_start
        assert credential.expected_passwords_needed_to_start == relaunch_pg.passwords_needed_to_start

        # relaunch the job and wait for completion
        payload = dict(ssh_password=testsetup.credentials['ssh']['password'],
                       ssh_key_unlock=testsetup.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       become_password=testsetup.credentials['ssh']['become_password'])
        job_pg = job_with_multi_ask_credential_and_password_in_payload.relaunch(payload).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_relaunch_with_multi_ask_credential_and_without_passwords(self, job_with_multi_ask_credential_and_password_in_payload):  # NOQA
        """Verify that relaunching a job with a multi-ask credential fails when not supplied with passwords."""
        # get relaunch page
        relaunch_pg = job_with_multi_ask_credential_and_password_in_payload.get_related('relaunch')

        # determine expected passwords
        credential = job_with_multi_ask_credential_and_password_in_payload.get_related('credential')

        # assert expected values in relaunch_pg.passwords_needed_to_start
        assert credential.expected_passwords_needed_to_start == relaunch_pg.passwords_needed_to_start

        # relaunch the job
        exc_info = pytest.raises(towerkit.exceptions.BadRequest, relaunch_pg.post, {})
        result = exc_info.value[1]

        # assert expected error responses
        assert 'passwords_needed_to_start' in result, \
            "Expecting 'passwords_needed_to_start' in API response when " \
            "relaunching a job, without provided credential " \
            "passwords. %s" % json.dumps(result)

        # assert expected values in response
        assert credential.expected_passwords_needed_to_start == result['passwords_needed_to_start']

    def test_relaunch_uses_extra_vars_from_job(self, job_with_extra_vars):
        """Verify that when you relaunch a job containing extra_vars in the
        launch-time payload, the resulting extra_vars *and* the job_template
        extra_vars are used.
        """
        relaunch_pg = job_with_extra_vars.get_related('relaunch')

        # assert values on relaunch resource
        assert not relaunch_pg.passwords_needed_to_start

        # relaunch the job and wait for completion
        relaunched_job_pg = job_with_extra_vars.relaunch().wait_until_completed()

        # assert success
        assert relaunched_job_pg.is_successful, "Job unsuccessful - %s" % relaunched_job_pg

        # coerce extra_vars into a dictionary
        try:
            job_extra_vars = json.loads(job_with_extra_vars.extra_vars)
        except ValueError:
            job_extra_vars = {}

        try:
            relaunch_extra_vars = json.loads(relaunched_job_pg.extra_vars)
        except ValueError:
            relaunch_extra_vars = {}

        # assert the extra_vars on the relaunched job, match the extra_vars
        # used in the original job
        assert set(relaunch_extra_vars) == set(job_extra_vars), \
            "The extra_vars on a relaunched job should match the extra_vars on the job being relaunched (%s != %s)" % \
            (relaunch_extra_vars, job_extra_vars)

    @pytest.mark.github("https://github.com/ansible/tower-qa/issues/1249")
    def test_password_survey_launched_with_empty_extra_vars(self, factories):
        """Confirms that password surveys with defaults are displayed (and encrypted) when
        job template is launched with empty extra_vars, and those without defaults are not.
        """
        survey = [dict(required=False,
                       question_name="{} - What's the password?".format(i),
                       variable='secret{}'.format(i),
                       type='password',
                       default='visible' if i % 2 else None) for i in range(10)]
        jt = factories.job_template()
        jt.add_survey(spec=survey)
        job = jt.launch(dict(extra_vars={}))
        assert(job.wait_until_completed().is_successful)
        extra_vars = json.loads(job.extra_vars)

        # only half of passwords had default values
        assert(len(extra_vars) == 5), "extra_vars found to be undesired length: {0}".format(extra_vars)

        assert(all([val == "$encrypted$" for val in extra_vars.values()])
               ), "Undesired values for extra_vars detected: {0}".format(extra_vars)

    def test_survey_defaults_dont_meet_length_requirements(self, factories):
        """Confirms that default survey spec variables that don't meet length requirements aren't provided to job"""
        jt = factories.job_template()
        spec = [dict(required=False, question_name="Question the First.",
                     variable='test_var_one', type='text', min=3, default=''),
                dict(required=False, question_name="Question the Second.",
                     variable='test_var_two', type='text', max=3, default='four'),
                dict(required=False, question_name="Question the Third.",
                     variable='test_var_three', type='text', min=0, default='abc')]
        jt.add_survey(spec=spec)
        job = jt.launch().wait_until_completed()
        assert job.is_successful
        assert job.extra_vars == json.dumps(dict(test_var_three='abc'))

    @pytest.mark.requires_isolation
    @pytest.mark.requires_single_instance
    @pytest.mark.ansible_integration
    def test_cancel_pending_job(self, job_with_status_pending):
        """Verify the job->cancel endpoint behaves as expected when canceling a
        pending/queued job
        """
        cancel_pg = job_with_status_pending.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel job (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel job
        cancel_pg.post()

        # wait for job to complete
        job_with_status_pending = job_with_status_pending.wait_until_completed()

        assert job_with_status_pending.status == 'canceled', \
            "Unexpected job status after cancelling (expected 'canceled') - " \
            "%s" % job_with_status_pending

        # Make sure the ansible-playbook did not start

        # Inspect the job_events and assert that the playbook_on_start
        # event was never received.  If 'playbook_on_start' event appears, then
        # ansible-playbook started, and the job was not cancelled in the
        # 'pending' state.
        job_events = job_with_status_pending.get_related('job_events', event="playbook_on_start")
        assert job_events.count == 0, "The pending job was successfully " \
            "canceled, but a 'playbook_on_start' host_event was received. " \
            "It appears that the job was not cancelled while in pending."

    @pytest.mark.ansible_integration
    def test_cancel_running_job(self, job_with_status_running):
        """Verify the job->cancel endpoint behaves as expected when canceling a
        running job
        """
        cancel_pg = job_with_status_running.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel job (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel job
        cancel_pg.post()

        # wait for job to complete
        job_with_status_running = job_with_status_running.wait_until_completed()

        assert job_with_status_running.status == 'canceled', \
            "Unexpected job status after cancelling job (expected status: canceled) - %s" % \
            job_with_status_running

        # Make sure the ansible-playbook did not complete

        # First, inspect the job_events and assert that the playbook_on_stats
        # event was never received.  If 'playbook_on_stats' event appears, then
        # ansible-playbook completed, despite the job status being marked as
        # 'canceled'.
        job_events = job_with_status_running.get_related('job_events', event="playbook_on_stats")
        assert job_events.count == 0, "The job was successfully canceled, but a" \
            "'playbook_on_stats' host_event was received.  It appears that the " \
            "ansible-playbook didn't cancel as expected."

        # Second, be sure the standard "PLAY RECAP" is missing from standard
        # output
        assert "PLAY RECAP ************" not in job_with_status_running.result_stdout

    def test_cancel_completed_job(self, job_with_status_completed):
        """Verify the job->cancel endpoint behaves as expected when canceling a
        completed job
        """
        cancel_pg = job_with_status_completed.get_related('cancel')

        # assert not can_cancel
        assert not cancel_pg.can_cancel, \
            "Unexpectedly able to cancel a completed job (can_cancel:%s)" % \
            cancel_pg.can_cancel

        # assert MethodNotAllowed when attempting to cancel
        with pytest.raises(towerkit.exceptions.MethodNotAllowed):
            cancel_pg.post()

    def test_jobs_persist_beyond_job_template_deletion(self, job_template):
        """Verify that jobs presist beyond their JT deletion."""
        job = job_template.launch().wait_until_completed()
        job_template.delete()

        # verify that our job persists
        job.get()

    @pytest.mark.parametrize('resource', ['project', 'custom_inventory_source'])
    def test_cascade_delete_update_unified_jobs(self, request, resource):
        """Verify that project and inventory updates get cascade deleted with their UJT deletion."""
        resource = request.getfuncargvalue(resource)
        update = resource.update().wait_until_completed()

        # delete unified job template
        if resource.type == 'project':
            resource.delete()
        else:
            resource.related.inventory.delete().wait_until_deleted()

        # verify that update cascade deleted
        with pytest.raises(towerkit.exceptions.NotFound):
            update.get()

    def test_delete_running_job_with_orphaned_project(self, factories, user_password):
        """Confirms that JT w/ cross org inventory and orphaned project deletion attempt triggers Forbidden"""
        org = factories.organization()
        operator = factories.user(organization=org)
        org.add_admin(operator)

        orphaned_project = factories.project(organization=None)
        cross_inventory = factories.inventory(organization=factories.organization())
        job_template = factories.job_template(organization=org,
                                              project=orphaned_project,
                                              inventory=cross_inventory)

        job_template.set_object_roles(operator, "execute")
        with self.current_user(operator.username, user_password):
            job = job_template.launch()
            with pytest.raises(towerkit.exceptions.Forbidden):
                job.delete()


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Scan_Job(Base_Api_Test):
    """Tests for scan jobs."""

    pytestmark = pytest.mark.usefixtures('authtoken')

    @pytest.mark.github("https://github.com/ansible/tower-qa/issues/1251", raises=AssertionError)
    @pytest.mark.ansible_integration
    def test_scan_job(self, install_enterprise_license_unlimited, scan_job_template):
        """Verifies that a default scan job populates fact_versions with the default three scan modules."""
        # obtain initial fact results
        fact_versions_pg = scan_job_template.get_related('inventory').get_related('hosts').results[0].get_related('fact_versions')
        initial_fact_versions = fact_versions_pg.results

        # launch the scan job and check that the job is successful
        job_pg = scan_job_template.launch().wait_until_completed()
        assert job_pg.is_successful, "Scan job unexpected failed - %s." % job_pg

        # verify that we have three new fact scans
        final_fact_versions = fact_versions_pg.get().results
        new_facts = set(final_fact_versions) - set(initial_fact_versions)
        confirm_fact_modules_present(new_facts, ansible=1, packages=1, services=1)

    @pytest.mark.github("https://github.com/ansible/tower-qa/issues/1251", raises=AssertionError)
    @pytest.mark.ansible_integration
    def test_file_scan_job(self, install_enterprise_license_unlimited, files_scan_job_template):
        """Tests file scan jobs."""
        # obtain intial fact results
        fact_versions_pg = files_scan_job_template.get_related('inventory').get_related('hosts').results[0].get_related('fact_versions')
        initial_fact_versions = fact_versions_pg.results

        # launch the scan job and check that the job is successful
        job_pg = files_scan_job_template.launch().wait_until_completed()
        assert job_pg.is_successful, "Files scan job unexpected failed - %s." % job_pg

        # verify that we have four new fact scans
        final_fact_versions = fact_versions_pg.get().results
        new_facts = set(final_fact_versions) - set(initial_fact_versions)
        confirm_fact_modules_present(new_facts, ansible=1, packages=1, services=1, files=1)

    @pytest.mark.github("https://github.com/ansible/tower-qa/issues/1251", raises=AssertionError)
    @pytest.mark.ansible_integration
    def test_recursive_file_scan_job(self, install_enterprise_license_unlimited, scan_job_template):
        """Tests that recursive file scan jobs pick up nested files"""
        # obtain intial fact results
        fact_versions_pg = scan_job_template.get_related('inventory').get_related('hosts').results[0].get_related('fact_versions')
        initial_fact_versions = fact_versions_pg.results

        # create a recursive file scan job template
        variables = dict(scan_file_paths="/tmp,/bin", scan_use_recursive="true")
        scan_job_template.patch(extra_vars=json.dumps(variables))

        # launch the scan job and check that the job is successful
        job_pg = scan_job_template.launch().wait_until_completed()
        assert job_pg.is_successful, "Scan job unexpected failed - %s." % job_pg

        # verify that we have four new fact scans
        final_fact_versions = fact_versions_pg.get().results
        new_facts = set(final_fact_versions) - set(initial_fact_versions)
        confirm_fact_modules_present(new_facts, ansible=1, packages=1, services=1, files=1)

        # check that a specific recursive file exists in fact results
        files_fact_version_pg = filter(lambda x: x.module == "files", new_facts)
        files_fact_view_pg = files_fact_version_pg[0].get_related('fact_view')
        assert any(fact.path == "/bin/ls" for fact in files_fact_view_pg.facts), \
            "Did not find target file 'bin/ls' after running recursive file scan. Results: %s." % files_fact_view_pg.fact

    @pytest.mark.github("https://github.com/ansible/tower-qa/issues/1251", raises=AssertionError)
    @pytest.mark.ansible_integration
    def test_file_scan_job_with_checksums(self, install_enterprise_license_unlimited, scan_job_template):
        """Tests that checksum file scan jobs include checksums."""
        # obtain intial fact results
        fact_versions_pg = scan_job_template.get_related('inventory').get_related('hosts').results[0].get_related('fact_versions')
        initial_fact_versions = fact_versions_pg.results

        # create a file scan job template with checksums
        variables = dict(scan_file_paths="/tmp,/bin", scan_use_checksum="true")
        scan_job_template.patch(extra_vars=json.dumps(variables))

        # launch the scan job and check that the job is successful
        job_pg = scan_job_template.launch().wait_until_completed()
        assert job_pg.is_successful, "Scan job unexpected failed - %s." % job_pg

        # verify that we have four new fact scans
        final_fact_versions = fact_versions_pg.get().results
        new_facts = set(final_fact_versions) - set(initial_fact_versions)
        confirm_fact_modules_present(new_facts, ansible=1, packages=1, services=1, files=1)

        # assert facts with checksum data exist
        files_fact_version_pg = filter(lambda x: x.module == "files", new_facts)
        files_fact_view_pg = files_fact_version_pg[0].get_related('fact_view')
        file_checksums = [x for x in files_fact_view_pg.facts if 'checksum' in x]
        assert len(file_checksums) > 0, "No files with checksums found after running a checksum scan job - %s." % file_checksums

    @pytest.mark.github("https://github.com/ansible/tower-qa/issues/1251", raises=AssertionError)
    @pytest.mark.ansible_integration
    def test_custom_scan_job(self, install_enterprise_license_unlimited, job_template):
        """Tests custom scan jobs."""
        # obtain intial fact results
        fact_versions_pg = job_template.get_related('inventory').get_related('hosts').results[0].get_related('fact_versions')
        initial_fact_versions = fact_versions_pg.results

        # create custom scan job template
        custom_scan_job_template = job_template.patch(playbook="scan_custom.yml", job_type="scan")

        # launch the scan job and check that the job is successful
        job_pg = custom_scan_job_template.launch().wait_until_completed()
        assert job_pg.is_successful, "Scan job unexpected failed - %s." % job_pg

        # verify that we have one new fact scan
        final_fact_versions = fact_versions_pg.get().results
        new_facts = set(final_fact_versions) - set(initial_fact_versions)
        confirm_fact_modules_present(new_facts, foo=1)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Env(Base_Api_Test):
    """Verify that credentials are properly passed to playbooks as
    environment variables ('job_env').
    """

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_job_env_with_cloud_credential(self, job_template_with_cloud_credential):
        """Verify that job_env has the expected cloud_credential variables.

        Note: Tower doesn't set environmental variables for CloudForms and Satellite6.
        """
        # get cloud_credential
        cloud_credential = job_template_with_cloud_credential.get_related('cloud_credential')

        # launch job and assert successful
        job_pg = job_template_with_cloud_credential.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s " % job_pg

        # assert expected environment variables and their values
        if cloud_credential.kind == 'aws':
            self.has_credentials('cloud', cloud_credential.kind, ['username'])
            expected_env_vars = dict(
                AWS_ACCESS_KEY_ID=self.credentials['cloud'][cloud_credential.kind]['username'],
                AWS_SECRET_ACCESS_KEY=u'**********'
            )
        elif cloud_credential.kind == 'gce':
            self.has_credentials('cloud', cloud_credential.kind, ['username', 'project'])
            expected_env_vars = dict(
                GCE_EMAIL=self.credentials['cloud'][cloud_credential.kind]['username'],
                GCE_PROJECT=self.credentials['cloud'][cloud_credential.kind]['project'],
                GCE_PEM_FILE_PATH=lambda x: re.match(r'^/tmp/awx_\w+/tmp\w+', x)
            )
        elif cloud_credential.kind == 'azure':
            self.has_credentials('cloud', 'azure_classic', ['username'])
            expected_env_vars = dict(
                AZURE_SUBSCRIPTION_ID=self.credentials['cloud']['azure_classic']['username'],
                AZURE_CERT_PATH=lambda x: re.match(r'^/tmp/awx_\w+/tmp\w+', x)
            )
        elif cloud_credential.kind == 'azure_rm' and azure_type(cloud_credential) == 'azure':
            self.has_credentials('cloud', 'azure', ['subscription_id', 'client_id', 'secret', 'tenant'])
            expected_env_vars = dict(
                AZURE_CLIENT_ID=self.credentials['cloud']['azure']['client_id'],
                AZURE_TENANT=self.credentials['cloud']['azure']['tenant'],
                AZURE_SUBSCRIPTION_ID=self.credentials['cloud']['azure']['subscription_id'],
                AZURE_SECRET=u'**********',
            )
        elif cloud_credential.kind == 'azure_rm' and azure_type(cloud_credential) == 'azure_ad':
            self.has_credentials('cloud', 'azure_ad', ['subscription_id', 'ad_user', 'password'])
            expected_env_vars = dict(
                AZURE_SUBSCRIPTION_ID=self.credentials['cloud']['azure']['subscription_id'],
                AZURE_AD_USER=self.credentials['cloud']['azure_ad']['ad_user'],
                AZURE_PASSWORD=u'**********',
            )
        elif cloud_credential.kind == 'vmware':
            self.has_credentials('cloud', cloud_credential.kind, ['username', 'host'])
            expected_env_vars = dict(
                VMWARE_USER=self.credentials['cloud'][cloud_credential.kind]['username'],
                VMWARE_PASSWORD=u'**********',
                VMWARE_HOST=self.credentials['cloud'][cloud_credential.kind]['host']
            )
        elif cloud_credential.kind == 'openstack':
            if "openstack-v2" in cloud_credential.name:
                self.has_credentials('cloud', 'openstack_v2', ['username', 'host', 'project'])
            elif "openstack-v3" in cloud_credential.name:
                self.has_credentials('cloud', 'openstack_v3', ['username', 'host', 'project', 'domain'])
            else:
                raise ValueError("Unhandled OpenStack credential: %s" % cloud_credential.name)
            expected_env_vars = dict(
                OS_CLIENT_CONFIG_FILE=lambda x: re.match(r'^/tmp/awx_\w+/tmp\w+', x)
            )
        elif cloud_credential.kind in ('cloudforms', 'satellite6'):
            self.has_credentials('cloud', cloud_credential.kind, ['host', 'username', 'password'])
            expected_env_vars = dict()
        else:
            raise ValueError("Unhandled cloud type: %s" % cloud_credential.kind)

        # assert the expected job_env variables are present
        confirm_job_env(job_pg, expected_env_vars)

    def test_job_env_with_network_credential(self, job_template_with_network_credential, expected_net_env_vars):
        """Verify that job_env has the expected network_credential variables."""
        # get cloud_credential
        network_credential = job_template_with_network_credential.get_related('network_credential')

        # launch job and assert successful
        job_pg = job_template_with_network_credential.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # assert the expected job_env variables are present
        expected_env_vars = expected_net_env_vars(network_credential)
        confirm_job_env(job_pg, expected_env_vars)
