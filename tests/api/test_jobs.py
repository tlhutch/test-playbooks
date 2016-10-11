# -*- coding: utf-8 -*-

import re
import types
import json
import logging
import pytest
import fauxfactory
import qe.tower.inventory
from dateutil.parser import parse
from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def job_sleep(request, job_template_sleep):
    '''
    Launch the job_template_sleep and return a job resource.
    '''
    return job_template_sleep.launch()


@pytest.fixture(scope="function")
def job_with_status_pending(job_template_sleep, pause_awx_task_system):
    '''
    Wait for job_sleep to move from new to queued, and return the job.
    '''
    return job_template_sleep.launch().wait_until_started()


@pytest.fixture(scope="function")
def job_with_status_running(request, job_sleep):
    '''
    Wait for job_sleep to move from queued to running, and return the job.
    '''
    return job_sleep.wait_until_status('running')


@pytest.fixture(scope="function")
def job_with_multi_ask_credential_and_password_in_payload(request, job_template_multi_ask, testsetup):
    '''
    Launch job_template_multi_ask with passwords in the payload.
    '''
    launch_pg = job_template_multi_ask.get_related("launch")

    # determine whether sudo or su was used
    credential = job_template_multi_ask.get_related('credential')

    # assert expected values in launch_pg.passwords_needed_to_start
    assert credential.expected_passwords_needed_to_start == launch_pg.passwords_needed_to_start

    # build launch payload
    payload = dict(ssh_password=testsetup.credentials['ssh']['password'],
                   ssh_key_unlock=testsetup.credentials['ssh']['encrypted']['ssh_key_unlock'],
                   vault_password=testsetup.credentials['ssh']['vault_password'],
                   become_password=testsetup.credentials['ssh']['become_password'])

    # launch job_template
    result = launch_pg.post(payload)

    # find and return specific job_pg
    jobs_pg = job_template_multi_ask.get_related('jobs', id=result.json['job'])
    assert jobs_pg.count == 1, "Unexpected number of jobs returned (%s != 1)" % jobs_pg.count
    return jobs_pg.results[0]


@pytest.fixture(scope="function", params=['project', 'inventory', 'credential'])
def job_with_deleted_related(request, job_with_status_completed):
    '''Creates and deletes an related attribute of a job'''
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
def project_django(request, authtoken, organization):
    # Create project
    payload = dict(name="django.git - %s" % fauxfactory.gen_utf8(),
                   scm_type='git',
                   scm_url='https://github.com/ansible-test/django.git',
                   scm_clean=False,
                   scm_delete_on_update=True,
                   scm_update_on_launch=True,)
    obj = organization.get_related('projects').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def job_template_with_project_django(job_template, project_django):
    project_django.wait_until_completed()
    return job_template.patch(project=project_django.id, playbook='ping.yml')


@pytest.fixture(scope="function")
def project_with_scm_update_on_launch(request, project_ansible_playbooks_git):
    return project_ansible_playbooks_git.patch(scm_update_on_launch=True)


@pytest.fixture(scope="function")
def another_custom_group(request, authtoken, api_groups_pg, inventory, inventory_script):
    payload = dict(name="custom-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="Custom Group %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   variables=json.dumps(dict(my_group_variable=True)))
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Set the inventory_source
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='custom',
                     source_script=inventory_script.id)
    return obj


@pytest.fixture(scope="function")
def job_template_with_cloud_credential(request, job_template, cloud_credential):
    job_template.patch(cloud_credential=cloud_credential.id)
    return job_template


@pytest.fixture(scope="function")
def job_template_with_network_credential(request, job_template, network_credential):
    job_template.patch(network_credential=network_credential.id)
    return job_template


@pytest.fixture(scope="function")
def cloud_inventory_job_template(request, job_template, cloud_group):
    # Substitute in no-op playbook that does not attempt to connect to host
    job_template.patch(playbook='debug.yml')
    return job_template


@pytest.fixture(scope="function")
def expected_net_env_vars(testsetup):
    """Returns a list of our expected network job env variables.
    """
    def func(network_credential):
        expected_env_vars = dict()
        if getattr(network_credential, "username", None):
            expected_env_vars["ANSIBLE_NET_USERNAME"] = testsetup.credentials['network']['username']
        if getattr(network_credential, "password", None):
            expected_env_vars["ANSIBLE_NET_PASSWORD"] = testsetup.credentials['network']['password']
        if getattr(network_credential, "authorize", None):
            expected_env_vars["ANSIBLE_NET_AUTHORIZE"] = "1"
        else:
            expected_env_vars["ANSIBLE_NET_AUTHORIZE"] = "0"
        if getattr(network_credential, "authorize_password", None):
            expected_env_vars["ANSIBLE_NET_AUTHORIZE_PASSWORD"] = testsetup.credentials['network']['authorize']
        return expected_env_vars
    return func


def confirm_fact_modules_present(facts, **kwargs):
    '''Convenience function to assess fact module contents.'''
    assert len(facts) == len(kwargs), "Unexpected number of new facts found ..."
    module_names = [x.module for x in facts]
    for (mod_name, mod_count) in kwargs.items():
        assert module_names.count(mod_name) == mod_count, "Unexpected number of facts found (%d) for module %s" % (mod_count, mod_name)


def assess_job_event_pg_for_no_log(job_event_pg):
    '''Convenience function to assess job_event_pg contents in testing no_log.'''
    result = job_event_pg.event_data.get('res')
    if not result:
        if "skipped task" in job_event_pg.task:
            return
        raise Exception("Unexpected condition: event_data.res not included in job_event for non-skipped task. "
                        "Possible integration test or schema change detected.")
    # For item tasks with no_log
    elif result.get('_ansible_no_log', None):
        assert 'item' not in result
        for item in ['cmd', 'censored']:
            if item in result:
                assert result[item] in ["echo <censored>",
                                        "the output has been hidden due to the fact that "
                                        "'no_log: true' was specified for this result"]
    # For item tasks without no_log
    else:
        for item in [item for item in ['item', 'cmd', 'stdout'] if item in result and item != 'stdout_lines']:
            assert 'LOG_ME' in result[item]
        if 'invocation' in result:
            assert 'LOG_ME' in result['invocation']['module_args']['_raw_params']
        if 'stdout_lines' in result:
            assert 'LOG_ME' in result['stdout_lines'][0]


def azure_type(azure_credential):
    '''Convenience function that returns our type of new-style Azure credential'''
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

    def test_utf8(self, utf8_template):
        '''
        Verify that a playbook full of UTF-8 successfully works through Tower
        '''
        # launch job
        job_pg = utf8_template.launch_job()

        # wait for completion
        job_pg = job_pg.wait_until_completed(timeout=60 * 10)

        # assert successful completion of job
        assert job_pg.is_successful, "Job unsuccessful - %s " % job_pg

    def test_post_as_superuser(self, job_template, api_jobs_pg):
        '''
        Verify a superuser is able to create a job by POSTing to the /api/v1/jobs endpoint.
        '''
        # post a job
        job_pg = api_jobs_pg.post(job_template.json)

        # assert successful post
        assert job_pg.status == 'new'

    def test_post_as_non_superuser(self, non_superusers, user_password, api_jobs_pg, job_template):
        '''
        Verify a non-superuser is unable to create a job by POSTing to the /api/v1/jobs endpoint.
        '''
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(qe.exceptions.Forbidden_Exception):
                    api_jobs_pg.post(job_template.json)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3590')
    def test_relaunch_with_credential(self, job_with_status_completed):
        '''
        Verify relaunching a job with a valid credential no-ask credential.
        '''
        relaunch_pg = job_with_status_completed.get_related('relaunch')

        # assert values on relaunch resource
        assert not relaunch_pg.passwords_needed_to_start

        # relaunch the job and wait for completion
        job_pg = job_with_status_completed.relaunch().wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_relaunch_with_deleted_related(self, job_with_deleted_related):
        '''
        Verify relaunching a job whose related information has been deleted.
        '''
        # get relaunch page
        relaunch_pg = job_with_deleted_related.get_related('relaunch')

        # assert values on relaunch resource
        assert not relaunch_pg.passwords_needed_to_start

        # attempt to relaunch the job, should raise exception
        with pytest.raises(qe.exceptions.BadRequest_Exception):
            relaunch_pg.post()

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3590')
    def test_relaunch_with_multi_ask_credential_and_passwords_in_payload(self, job_with_multi_ask_credential_and_password_in_payload, testsetup):  # NOQA
        '''
        Verify that relaunching a job with a credential that includes ASK passwords, behaves as expected when
        supplying the necessary passwords in the relaunch payload.
        '''
        # get relaunch page
        relaunch_pg = job_with_multi_ask_credential_and_password_in_payload.get_related('relaunch')

        # determine expected passwords
        credential = job_with_multi_ask_credential_and_password_in_payload.get_related('credential')

        # assert expected values in relaunch_pg.passwords_needed_to_start
        assert credential.expected_passwords_needed_to_start == relaunch_pg.passwords_needed_to_start

        # relaunch the job and wait for completion
        payload = dict(ssh_password=testsetup.credentials['ssh']['password'],
                       ssh_key_unlock=testsetup.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       vault_password=testsetup.credentials['ssh']['vault_password'],
                       become_password=testsetup.credentials['ssh']['become_password'])
        job_pg = job_with_multi_ask_credential_and_password_in_payload.relaunch(payload).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_relaunch_with_multi_ask_credential_and_without_passwords(self, job_with_multi_ask_credential_and_password_in_payload):  # NOQA
        '''
        Verify that relaunching a job with a multi-ask credential fails when not supplied with passwords.
        '''
        # get relaunch page
        relaunch_pg = job_with_multi_ask_credential_and_password_in_payload.get_related('relaunch')

        # determine expected passwords
        credential = job_with_multi_ask_credential_and_password_in_payload.get_related('credential')

        # assert expected values in relaunch_pg.passwords_needed_to_start
        assert credential.expected_passwords_needed_to_start == relaunch_pg.passwords_needed_to_start

        # relaunch the job
        exc_info = pytest.raises(qe.exceptions.BadRequest_Exception, relaunch_pg.post, {})
        result = exc_info.value[1]

        # assert expected error responses
        assert 'passwords_needed_to_start' in result, \
            "Expecting 'passwords_needed_to_start' in API response when " \
            "relaunching a job, without provided credential " \
            "passwords. %s" % json.dumps(result)

        # assert expected values in response
        assert credential.expected_passwords_needed_to_start == result['passwords_needed_to_start']

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3590')
    def test_relaunch_uses_extra_vars_from_job(self, job_with_extra_vars):
        '''
        Verify that when you relaunch a job containing extra_vars in the
        launch-time payload, the resulting extra_vars *and* the job_template
        extra_vars are used.
        '''
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

    def test_password_survey_launched_with_empty_extra_vars(self, factories):
        """
        Confirms that password surveys with defaults are displayed (and encrypted) when
        job template is launched with empty extra_vars, and those without defaults are not.
        """
        survey = [dict(required=False,
                       question_name="{} - What's the password?".format(i),
                       variable='secret{}'.format(i),
                       type='password',
                       default='visible' if i % 2 else '') for i in range(10)]
        jt = factories.job_template().add_survey(spec=survey)
        job = jt.launch(dict(extra_vars={}))
        assert(job.wait_until_completed().is_successful)
        extra_vars = json.loads(job.extra_vars)

        # only half of passwords had default values
        assert(len(extra_vars) == 5), "extra_vars found to be undesired length: {0}".format(extra_vars)

        assert(all([val == "$encrypted$" for val in extra_vars.values()])
               ), "Undesired values for extra_vars detected: {0}".format(extra_vars)

    @pytest.mark.skip('https://github.com/ansible/tower-qa/issues/838')
    def test_cancel_pending_job(self, job_with_status_pending):
        '''
        Verify the job->cancel endpoint behaves as expected when canceling a
        pending/queued job
        '''
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

    def test_cancel_running_job(self, job_with_status_running):
        '''
        Verify the job->cancel endpoint behaves as expected when canceling a
        running job
        '''
        cancel_pg = job_with_status_running.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel job (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel job
        cancel_pg.post()

        # wait for job to complete
        job_with_status_running = job_with_status_running.wait_until_completed()

        assert job_with_status_running.status == 'canceled', "Unexpected job" \
            "status after cancelling job (expected status:canceled) - %s" % \
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
        '''
        Verify the job->cancel endpoint behaves as expected when canceling a
        completed job
        '''
        cancel_pg = job_with_status_completed.get_related('cancel')

        # assert not can_cancel
        assert not cancel_pg.can_cancel, \
            "Unexpectedly able to cancel a completed job (can_cancel:%s)" % \
            cancel_pg.can_cancel

        # assert Method_Not_Allowed when attempting to cancel
        with pytest.raises(qe.exceptions.Method_Not_Allowed_Exception):
            cancel_pg.post()

    def test_launch_with_inventory_update(self, job_template, cloud_group, host_local):
        '''
        Tests that job launches with inventory updates work with all cloud providers.
        '''
        job_template.patch(limit=host_local.name)
        cloud_group.get_related('inventory_source').patch(update_on_launch=True)

        # Assert that the cloud_group has not updated
        assert not cloud_group.get_related('inventory_source').last_updated

        # Launch job and check results
        job_pg = job_template.launch().wait_until_completed(timeout=60 * 3)
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # Assert that the inventory_update is marked as successful
        inv_source_pg = cloud_group.get_related('inventory_source')
        assert inv_source_pg.is_successful, "An inventory_update was launched, but the inventory_source is not successful - %s" % inv_source_pg

        # Assert that an inventory_update completed successfully
        inv_update_pg = inv_source_pg.get_related('last_update')
        assert inv_update_pg.is_successful, "An inventory_update was launched, but did not succeed - %s" % inv_update_pg

    def test_launch_with_scm_update(self, job_template, project_with_scm_update_on_launch):
        '''
        Tests that job launches with projects that have "Update on Launch" enabled work as expected.
        '''
        job_template.patch(project=project_with_scm_update_on_launch.id)

        # Remember last update
        initial_update_pg = project_with_scm_update_on_launch.get_related('last_update')

        # Launch job and check results
        job_pg = job_template.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

        # Assert a new scm update was launched
        updated_project_pg = project_with_scm_update_on_launch.get()
        final_update_pg = updated_project_pg.get_related('last_update')
        assert initial_update_pg.id != final_update_pg.id, "Update IDs are the same (%s = %s)" % (initial_update_pg.id, final_update_pg.id)

    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import json, time

# sleep helps us cancel the inventory update
time.sleep(60)
inventory = dict()

print json.dumps(inventory)
''')
    def test_cascade_cancel_with_inventory_update(self, job_template, custom_group):
        '''
        Tests that if you cancel an inventory update before it finishes that its dependent job fails.
        '''
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."

        # Launch job
        job_pg = job_template.launch()

        # Wait for the inventory_source to start
        inv_source_pg.wait_until_started()

        # Cancel inventory update
        inv_update_pg = inv_source_pg.get_related('current_update')
        cancel_pg = inv_update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "The inventory_update is not cancellable, it may have already completed - %s." % inv_update_pg.get()
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == inv_update_pg.type
        assert job_explanation['job_name'] == inv_update_pg.name
        assert job_explanation['job_id'] == str(inv_update_pg.id)

        # Assert inventory update and source canceled
        assert inv_update_pg.get().status == 'canceled', \
            "Unexpected job status after cancelling (expected 'canceled') - %s." % inv_update_pg.status
        assert inv_source_pg.get().status == 'canceled', \
            "Unexpected inventory_source status after cancelling (expected 'canceled') - %s." % inv_source_pg.status

    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import json, time

# sleep helps us cancel the inventory update
time.sleep(60)
inventory = dict()

print json.dumps(inventory)
''')
    def test_cascade_cancel_with_multiple_inventory_updates(self, job_template, custom_group, another_custom_group):
        '''
        Tests that if you cancel an inventory update before it finishes that its dependent jobs fail.
        '''
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)
        another_inv_source_pg = another_custom_group.get_related('inventory_source')
        another_inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."
        assert not another_inv_source_pg.last_updated, "another_inv_source_pg unexpectedly updated."

        # Launch job
        job_pg = job_template.launch()

        # Wait for the inventory sources to start
        inv_update_pg = inv_source_pg.wait_until_started().get_related('current_update')
        another_inv_update_pg = another_inv_source_pg.wait_until_started().get_related('current_update')
        inv_update_pg_started = parse(inv_update_pg.created)
        another_inv_update_pg_started = parse(another_inv_update_pg.created)

        # Identify the sequence of the inventory updates and navigate to cancel_pg
        if inv_update_pg_started > another_inv_update_pg_started:
            cancel_pg = another_inv_update_pg.get_related('cancel')
            assert cancel_pg.can_cancel, \
                "Inventory update is not cancellable, it may have already completed - %s." % another_inv_update_pg.get()
            # Set new set of vars
            first_inv_update_pg, first_inv_source_pg = another_inv_update_pg, another_inv_source_pg
            second_inv_update_pg, second_inv_source_pg = inv_update_pg, inv_source_pg
        else:
            cancel_pg = inv_update_pg.get_related('cancel')
            assert cancel_pg.can_cancel, \
                "Inventory update is not cancellable, it may have already completed - %s." % inv_update_pg.get()
            # Set new set of vars
            first_inv_update_pg, first_inv_source_pg = inv_update_pg, inv_source_pg
            second_inv_update_pg, second_inv_source_pg = another_inv_update_pg, another_inv_source_pg

        # Cancel the first inventory update
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == first_inv_update_pg.type
        assert job_explanation['job_name'] == first_inv_update_pg.name
        assert job_explanation['job_id'] == str(first_inv_update_pg.id)

        # Assert first inventory update and source cancelled
        assert first_inv_update_pg.get().status == 'canceled', \
            "Did not cancel job as expected (expected status:canceled) - %s." % first_inv_update_pg
        assert first_inv_source_pg.get().status == 'canceled', \
            "Did not cancel job as expected (expected status:canceled) - %s." % first_inv_source_pg

        # Assert second inventory update and source failed
        assert second_inv_update_pg.get().status == 'failed', \
            "Secondary inventory update not failed (status: %s)." % second_inv_update_pg.status
        assert second_inv_source_pg.get().status == 'failed', \
            "Secondary inventory update not failed (status: %s)." % second_inv_source_pg.status

        # Assess second update job_explanation
        assert second_inv_update_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % second_inv_update_pg.job_explanation
        try:
            inventory_job_explanation = json.loads(second_inv_update_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % inventory_job_explanation
        assert inventory_job_explanation['job_type'] == first_inv_update_pg.type
        assert inventory_job_explanation['job_name'] == first_inv_update_pg.name
        assert inventory_job_explanation['job_id'] == str(first_inv_update_pg.id)

    def test_cascade_cancel_with_project_update(self, job_template_with_project_django):
        '''
        Tests that if you cancel a SCM update before it finishes that its dependent job fails.
        '''
        project_pg = job_template_with_project_django.get_related('project')

        # Launch job
        job_pg = job_template_with_project_django.launch()

        # Wait for new update to start and cancel it
        project_update_pg = project_pg.wait_until_started().get_related('current_update')
        cancel_pg = project_update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "The project update is not cancellable, it may have already completed - %s." % project_update_pg.get()
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == project_update_pg.type
        assert job_explanation['job_name'] == project_update_pg.name
        assert job_explanation['job_id'] == str(project_update_pg.id)

        # Assert project update and project canceled
        assert project_update_pg.get().status == 'canceled', \
            "Unexpected project_update status after cancelling (expected 'canceled') - %s." % project_update_pg
        assert project_pg.get().status == 'canceled', \
            "Unexpected project status (expected status:canceled) - %s." % project_pg

    def test_cascade_cancel_project_update_with_inventory_and_project_updates(self, job_template_with_project_django, custom_group):
        '''
        Tests that if you cancel a scm update before it finishes that its dependent job
        fails. This test runs both inventory and SCM updates on job launch.
        '''
        project_pg = job_template_with_project_django.get_related('project')
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."

        # Launch job
        job_pg = job_template_with_project_django.launch()

        # Wait for new update to start and cancel it
        project_update_pg = project_pg.wait_until_started().get_related('current_update')
        cancel_pg = project_update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "The project update is not cancellable, it may have already completed - %s." % project_update_pg.get()
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s" % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == project_update_pg.type
        assert job_explanation['job_name'] == project_update_pg.name
        assert job_explanation['job_id'] == str(project_update_pg.id)

        # Assert project update and project cancelled
        assert project_update_pg.get().status == 'canceled', \
            "Unexpected job status after cancelling (expected 'canceled') - %s." % project_update_pg
        assert project_pg.get().status == 'canceled', \
            "Unexpected project status after cancelling (expected 'canceled') - %s." % project_pg

        # Assert inventory update and source successful
        inv_update_pg = inv_source_pg.wait_until_completed().get_related('last_update')
        assert inv_update_pg.is_successful, "Inventory update unexpectedly unsuccessful - %s." % inv_update_pg
        assert inv_source_pg.get().is_successful, "inventory_source unexpectedly unsuccessful - %s." % inv_source_pg

    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import json, time

# sleep helps us cancel the inventory update
time.sleep(60)
inventory = dict()

print json.dumps(inventory)
''')
    def test_cascade_cancel_inventory_update_with_inventory_and_project_updates(self, job_template, custom_group):
        '''
        Tests that if you cancel an inventory update before it finishes that its dependent job
        fails. This test runs both inventory and SCM updates on job launch.
        '''
        project_pg = job_template.get_related('project')
        project_pg.patch(update_on_launch=True)
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."

        # Launch job
        job_pg = job_template.launch()

        # Wait for the inventory_source to start
        inv_source_pg.wait_until_started()

        # Cancel inventory update
        inv_update_pg = inv_source_pg.get_related('current_update')
        cancel_pg = inv_update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "The inventory_update is not cancellable, it may have already completed - %s." % inv_update_pg.get()
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == inv_update_pg.type
        assert job_explanation['job_name'] == inv_update_pg.name
        assert job_explanation['job_id'] == str(inv_update_pg.id)

        # Assert project update and project successful
        project_update_pg = project_pg.get_related('last_update')
        assert project_update_pg.wait_until_completed().status == 'successful', "Project update unsuccessful - %s." % project_update_pg
        assert project_pg.get().status == 'successful', "Project unsuccessful - %s." % project_pg

        # Assert inventory update and source canceled
        assert inv_update_pg.get().status == "canceled", \
            "Unexpected inventory update_pg status after cancelling (expected 'canceled') - %s." % inv_update_pg
        assert inv_source_pg.get().status == "canceled", \
            "Unexpected inventory_source status after cancelling (expected 'canceled') - %s." % inv_source_pg

    def test_job_with_no_log(self, factories, ansible_version_cmp):
        '''
        Tests that jobs with 'no_log' censor the following:
        * jobs/N/job_events
        * jobs/N.result_stdout
        '''
        # Test for ansible-v2 or greater
        if ansible_version_cmp('2.0.0.0') < 0:
            pytest.skip("Only supported on ansible-2.0.0.0 (or newer)")

        job_template = factories.job_template(project__scm_url='https://github.com/ansible/ansible.git',
                                              playbook='test/integration/no_log_local.yml',
                                              inventory__localhost__name='testhost',
                                              verbosity=1)
        # Launch test job template
        job_pg = job_template.launch().wait_until_completed()
        assert(job_pg.is_successful), "Job unsuccessful - %s." % job_pg

        # Check job_events
        job_events_pg = job_pg.get_related('job_events', event__startswith='runner')
        for job_event_pg in job_events_pg.results:
            assess_job_event_pg_for_no_log(job_event_pg)

        # Check result_stdout
        log_count = job_pg.result_stdout.count('LOG_ME')
        assert(log_count == 21), ('Unexpected number of instances of "LOG_ME" in job_pg.result_stdout: expected 21, '
                                  'got {}'.format(log_count))
        censored_count = job_pg.result_stdout.count('censored')
        assert(censored_count == 12), ('Unexpected number of instances of "censored" in job_pg.result_stdout: expected '
                                       '12, got {}.'.format(censored_count))

    def test_job_with_async_events(self, factories, ansible_version_cmp):
        '''Tests that jobs with 'async' report their runner events'''
        if ansible_version_cmp('2.0.0.0') < 0:
            pytest.skip("test_async only supported on ansible-2.0.0.0 (or newer)")
        elif ansible_version_cmp('2.2.0.0') < 0:
            scm_branch = 'stable-2.1'
        else:
            scm_branch = 'devel'

        job_template = factories.job_template(project__scm_url='https://github.com/ansible/ansible.git',
                                              project__scm_branch=scm_branch,
                                              playbook='test/integration/non_destructive.yml',
                                              inventory__localhost__name='testhost',
                                              job_tags='test_async',
                                              verbosity=1)
        job = job_template.launch().wait_until_completed()
        # Async playbook includes task ('test exception module failure') which intentionally throws
        # an exception (which is ignored). Instead of using job.is_successful (which checks for exceptions
        # in the jobs stdout), check job status and failed field explicitly
        assert(job.status.lower() == 'successful' and not job.failed), "Job unsuccessful - {0}.".format(job)

        # Check job_events
        job_events = job.get_related('job_events', event__startswith='runner_on')
        test_events = [event for event in job_events.results if 'test_async' in event.task]
        assert(test_events), 'No "runner_on" events reported during test_async integration test execution'

        for test_event in test_events:
            assertion_error = 'Undesired job event for {0.task}: "{0.event}"'.format(test_event)
            if "skipped" in test_event.task:
                assert(test_event.event == 'runner_on_skipped'), assertion_error
            else:
                assert(test_event.event == 'runner_on_ok'), assertion_error

    def test_delete_running_job_with_orphaned_project(self, factories, set_roles, user_password):
        """Confirms that JT w/ cross org inventory and orphaned project deletion attempt triggers Forbidden"""
        org = factories.organization()
        operator = factories.user(organization=org)
        org.add_admin(operator)

        orphaned_project = factories.project(organization=None)
        cross_inventory = factories.inventory(organization=factories.organization())
        job_template = factories.job_template(organization=org,
                                              project=orphaned_project,
                                              inventory=cross_inventory)

        set_roles(operator, job_template, ['execute'])
        with self.current_user(operator.username, user_password):
            job = job_template.launch()
            with pytest.raises(qe.exceptions.Forbidden_Exception):
                job.delete()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3661')
@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Scan_Job(Base_Api_Test):
    '''Tests for scan jobs.'''
    pytestmark = pytest.mark.usefixtures('authtoken')

    def test_scan_job(self, install_enterprise_license_unlimited, scan_job_template):
        '''Verifies that a default scan job populates fact_versions with the default three scan modules.'''
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

    def test_file_scan_job(self, install_enterprise_license_unlimited, files_scan_job_template):
        '''Tests file scan jobs.'''
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

    def test_recursive_file_scan_job(self, install_enterprise_license_unlimited, scan_job_template):
        '''Tests that recursive file scan jobs pick up nested files'''
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

    def test_file_scan_job_with_checksums(self, install_enterprise_license_unlimited, scan_job_template):
        '''Tests that checksum file scan jobs include checksums.'''
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

    def test_custom_scan_job(self, install_enterprise_license_unlimited, job_template):
        '''Tests custom scan jobs.'''
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
    '''
    Verify that credentials are properly passed to playbooks as
    environment variables ('job_env').
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_job_env_with_cloud_credential(self, job_template_with_cloud_credential):
        '''
        Verify that job_env has the expected cloud_credential variables.

        Note: Tower doesn't set environmental variables for CloudForms and Satellite6.
        '''
        # get cloud_credential
        cloud_credential = job_template_with_cloud_credential.get_related('cloud_credential')

        # launch job and assert successful
        job_pg = job_template_with_cloud_credential.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s " % job_pg

        # assert expected environment variables and their values
        if cloud_credential.kind == 'aws':
            self.has_credentials('cloud', cloud_credential.kind, ['username'])
            expected_env_vars = dict(
                AWS_ACCESS_KEY=self.credentials['cloud'][cloud_credential.kind]['username'],
                AWS_SECRET_KEY=u'**********'
            )
        elif cloud_credential.kind == 'rax':
            self.has_credentials('cloud', cloud_credential.kind, ['username'])
            expected_env_vars = dict(
                RAX_USERNAME=self.credentials['cloud'][cloud_credential.kind]['username'],
                RAX_API_KEY=u'**********'
            )
        elif cloud_credential.kind == 'gce':
            self.has_credentials('cloud', cloud_credential.kind, ['username', 'project'])
            expected_env_vars = dict(
                GCE_EMAIL=self.credentials['cloud'][cloud_credential.kind]['username'],
                GCE_PROJECT=self.credentials['cloud'][cloud_credential.kind]['project'],
                GCE_PEM_FILE_PATH=lambda x: re.match(r'^/tmp/ansible_tower_\w+/tmp\w+', x)
            )
        elif cloud_credential.kind == 'azure':
            self.has_credentials('cloud', 'azure_classic', ['username'])
            expected_env_vars = dict(
                AZURE_SUBSCRIPTION_ID=self.credentials['cloud']['azure_classic']['username'],
                AZURE_CERT_PATH=lambda x: re.match(r'^/tmp/ansible_tower_\w+/tmp\w+', x)
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
                OS_CLIENT_CONFIG_FILE=lambda x: re.match(r'^/tmp/ansible_tower_\w+/tmp\w+', x)
            )
        elif cloud_credential.kind in ('cloudforms', 'satellite6'):
            self.has_credentials('cloud', cloud_credential.kind, ['host', 'username', 'password'])
            expected_env_vars = dict()
        else:
            raise ValueError("Unhandled cloud type: %s" % cloud_credential.kind)

        # assert the expected job_env variables are present
        for env_var, env_val in expected_env_vars.items():
            assert env_var in job_pg.job_env, \
                "Missing expected %s environment variable %s in job_env.\n%s" % \
                (cloud_credential.kind, env_var, json.dumps(job_pg.job_env, indent=2))
            if isinstance(env_val, types.FunctionType):
                is_correct = env_val(job_pg.job_env[env_var])
            else:
                is_correct = job_pg.job_env[env_var] == env_val

            assert is_correct, "Unexpected value for %s environment variable %s " \
                "in job_env ('%s')" % (cloud_credential.kind, env_var,
                                       job_pg.job_env[env_var])

    def test_job_env_with_network_credential(self, job_template_with_network_credential, expected_net_env_vars):
        '''
        Verify that job_env has the expected network_credential variables.
        '''
        # get cloud_credential
        network_credential = job_template_with_network_credential.get_related('network_credential')

        # launch job and assert successful
        job_pg = job_template_with_network_credential.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # assert the expected job_env variables are present
        expected_env_vars = expected_net_env_vars(network_credential)
        for env_var, env_val in expected_env_vars.items():
            assert env_var in job_pg.job_env, \
                "Missing expected network environment variable %s in job_env.\n%s" % \
                (env_var, json.dumps(job_pg.job_env, indent=2))
            assert job_pg.job_env[env_var] == env_val, \
                "Unexpected value for %s environment variable %s in job_env ('%s')" \
                % (network_credential.kind, env_var, job_pg.job_env[env_var])


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Update_On_Launch(Base_Api_Test):
    '''
    Verify that, when configured, inventory_updates and project_updates are
    initiated on job launch
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_inventory(self, cloud_inventory_job_template, cloud_group):
        '''Verify that an inventory_update is triggered by job launch'''

        # 1) Set update_on_launch
        inv_src_pg = cloud_group.get_related('inventory_source')
        inv_src_pg.patch(update_on_launch=True)
        assert inv_src_pg.update_cache_timeout == 0
        assert inv_src_pg.last_updated is None, "Not expecting inventory_source an have been updated - %s" % \
            json.dumps(inv_src_pg.json, indent=4)

        # 2) Update job_template to cloud inventory
        cloud_inventory_job_template.patch(inventory=cloud_group.inventory)

        # 3) Launch job_template and wait for completion
        cloud_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # 4) Ensure inventory_update was triggered
        inv_src_pg.get()
        assert inv_src_pg.last_updated is not None, "Expecting value for last_updated - %s" % \
            json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.last_job_run is not None, "Expecting value for last_job_run - %s" % \
            json.dumps(inv_src_pg.json, indent=4)

        # 5) Ensure inventory_update was successful
        last_update = inv_src_pg.get_related('last_update')
        assert last_update.is_successful, "last_update unsuccessful - %s" % last_update
        assert inv_src_pg.is_successful, "inventory_source unsuccessful - %s" % json.dumps(inv_src_pg.json, indent=4)

    def test_inventory_multiple(self, job_template, aws_inventory_source, rax_inventory_source):
        '''Verify that multiple inventory_update's are triggered by job launch'''

        # 1) Set update_on_launch
        aws_inventory_source.patch(update_on_launch=True)
        assert aws_inventory_source.update_on_launch
        assert aws_inventory_source.update_cache_timeout == 0
        assert aws_inventory_source.last_updated is None, "Not expecting inventory_source to have been updated - %s" % \
            json.dumps(aws_inventory_source.json, indent=4)
        rax_inventory_source.patch(update_on_launch=True)
        assert rax_inventory_source.update_on_launch
        assert rax_inventory_source.update_cache_timeout == 0
        assert rax_inventory_source.last_updated is None, "Not expecting inventory_source to have been updated - %s" % \
            json.dumps(rax_inventory_source.json, indent=4)

        # 2) Update job_template to cloud inventory
        #    Also, substitute in no-op playbook that does not attempt to connect to host
        assert rax_inventory_source.inventory == aws_inventory_source.inventory, \
            "The inventory differs between the two inventory sources"
        job_template.patch(inventory=aws_inventory_source.inventory, playbook='debug.yml')

        # 3) Launch job_template and wait for completion
        job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # 4) Ensure inventory_update was triggered
        aws_inventory_source.get()
        assert aws_inventory_source.last_updated is not None, "Expecting value for aws_inventory_source last_updated - %s" % \
            json.dumps(aws_inventory_source.json, indent=4)
        assert aws_inventory_source.last_job_run is not None, "Expecting value for aws_inventory_source last_job_run - %s" % \
            json.dumps(aws_inventory_source.json, indent=4)

        rax_inventory_source.get()
        assert rax_inventory_source.last_updated is not None, "Expecting value for rax_inventory_source last_updated - %s" % \
            json.dumps(rax_inventory_source.json, indent=4)
        assert rax_inventory_source.last_job_run is not None, "Expecting value for rax_inventory_source last_job_run - %s" % \
            json.dumps(rax_inventory_source.json, indent=4)

        # 5) Ensure inventory_update was successful
        last_update = aws_inventory_source.get_related('last_update')
        assert last_update.is_successful, "aws_inventory_source -> last_update unsuccessful - %s" % last_update
        assert aws_inventory_source.is_successful, "inventory_source unsuccessful - %s" % \
            json.dumps(aws_inventory_source.json, indent=4)

        # assert last_update successful
        last_update = rax_inventory_source.get_related('last_update')
        assert last_update.is_successful, "rax_inventory_source -> last_update unsuccessful - %s" % last_update
        assert rax_inventory_source.is_successful, "inventory_source unsuccessful - %s" % \
            json.dumps(rax_inventory_source.json, indent=4)

    def test_inventory_cache_timeout(self, cloud_inventory_job_template, cloud_group):
        '''Verify that an inventory_update is not triggered by job launch if the cache is still valid'''

        # 1) Set update_on_launch and a 5min update_cache_timeout
        inv_src_pg = cloud_group.get_related('inventory_source')
        cache_timeout = 60 * 5
        inv_src_pg.patch(update_on_launch=True, update_cache_timeout=cache_timeout)
        assert inv_src_pg.update_cache_timeout == cache_timeout
        assert inv_src_pg.last_updated is None, "Not expecting inventory_source an have been updated - %s" % \
            json.dumps(inv_src_pg.json, indent=4)

        # 2) Update job_template to cloud inventory
        cloud_inventory_job_template.patch(inventory=cloud_group.inventory)

        # 3) Launch job_template and wait for completion
        cloud_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # 4) Ensure inventory_update was triggered
        inv_src_pg.get()
        assert inv_src_pg.last_updated is not None, "Expecting value for last_updated - %s" % \
            json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.last_job_run is not None, "Expecting value for last_job_run - %s" % \
            json.dumps(inv_src_pg.json, indent=4)
        last_updated = inv_src_pg.last_updated
        last_job_run = inv_src_pg.last_job_run

        # 5) Launch job_template and wait for completion
        cloud_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # 6) Ensure inventory_update was *NOT* triggered
        inv_src_pg.get()
        assert inv_src_pg.last_updated == last_updated, \
            "An inventory_update was unexpectedly triggered (last_updated changed)- %s" % \
            json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.last_job_run == last_job_run, \
            "An inventory_update was unexpectedly triggered (last_job_run changed)- %s" % \
            json.dumps(inv_src_pg.json, indent=4)

    def test_project(self, project_ansible_playbooks_git, job_template_ansible_playbooks_git):
        '''Verify that a project_update is triggered by job launch'''

        # 1) set scm_update_on_launch for the project
        project_ansible_playbooks_git.patch(scm_update_on_launch=True)
        assert project_ansible_playbooks_git.scm_update_on_launch
        assert project_ansible_playbooks_git.scm_update_cache_timeout == 0
        last_updated = project_ansible_playbooks_git.last_updated

        # 2) Launch job_template and wait for completion
        job_template_ansible_playbooks_git.launch_job().wait_until_completed(timeout=50 * 10)

        # 3) Ensure project_update was triggered and successful
        project_ansible_playbooks_git.get()
        assert project_ansible_playbooks_git.last_updated != last_updated, \
            "A project_update was not triggered, last_updated (%s) remains unchanged" % last_updated
        assert project_ansible_playbooks_git.is_successful, "project unsuccessful - %s" % \
            json.dumps(project_ansible_playbooks_git.json, indent=4)

    def test_project_cache_timeout(self, project_ansible_playbooks_git, job_template_ansible_playbooks_git):
        '''Verify that a project_update is not triggered when the cache_timeout has not exceeded'''

        # 1) set scm_update_on_launch for the project
        cache_timeout = 60 * 5
        project_ansible_playbooks_git.patch(scm_update_on_launch=True, scm_update_cache_timeout=cache_timeout)
        assert project_ansible_playbooks_git.scm_update_on_launch
        assert project_ansible_playbooks_git.scm_update_cache_timeout == cache_timeout
        assert project_ansible_playbooks_git.last_updated is not None
        last_updated = project_ansible_playbooks_git.last_updated

        # 2) Launch job_template and wait for completion
        job_template_ansible_playbooks_git.launch_job().wait_until_completed(timeout=50 * 10)

        # 3) Ensure project_update was *NOT* triggered
        project_ansible_playbooks_git.get()
        assert project_ansible_playbooks_git.last_updated == last_updated, \
            "A project_update happened, but was not expected"

    def test_inventory_and_project(self, project_ansible_playbooks_git, job_template_ansible_playbooks_git,
                                   cloud_group):
        '''Verify that a project_update and inventory_update are triggered by job launch'''

        # 1) Set scm_update_on_launch for the project
        project_ansible_playbooks_git.patch(scm_update_on_launch=True)
        assert project_ansible_playbooks_git.scm_update_on_launch
        last_updated = project_ansible_playbooks_git.last_updated

        # 2) Set update_on_launch for the inventory
        inv_src_pg = cloud_group.get_related('inventory_source')
        inv_src_pg.patch(update_on_launch=True)
        assert inv_src_pg.update_on_launch

        # 3) Update job_template to cloud inventory
        #    Also, substitute in no-op playbook that does not attempt to connect to host
        job_template_ansible_playbooks_git.patch(inventory=cloud_group.inventory, playbook='debug.yml')

        # 4) Launch job_template and wait for completion
        job_template_ansible_playbooks_git.launch_job().wait_until_completed(timeout=50 * 10)

        # 5) Ensure project_update was triggered and is successful
        project_ansible_playbooks_git.get()
        assert project_ansible_playbooks_git.last_updated != last_updated, \
            "project_update was not triggered - %s" % json.dumps(project_ansible_playbooks_git.json, indent=4)
        assert project_ansible_playbooks_git.is_successful, "project unsuccessful - %s" % \
            json.dumps(project_ansible_playbooks_git.json, indent=4)

        # 6) Ensure inventory_update was triggered and is successful
        inv_src_pg.get()
        assert inv_src_pg.last_updated is not None, "Expecting value for last_updated - %s" % \
            json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.last_job_run is not None, "Expecting value for last_job_run - %s" % \
            json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.is_successful, "inventory_source unsuccessful - %s" % json.dumps(inv_src_pg.json, indent=4)
