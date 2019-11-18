import logging
import re
import json

from awxkit import exceptions as exc
from awxkit.utils import poll_until
import fauxfactory
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.fixture(scope="function", params=['cleanup_jobs_with_status_completed',
                                          'custom_inventory_update_with_status_completed',
                                          'project_update_with_status_completed',
                                          'job_with_status_completed',
                                          'ad_hoc_with_status_completed'])
def unified_job_with_stdout(request):
    """Returns a completed unified job with job stdout."""
    return request.getfixturevalue(request.param)


def assess_created_elements(elements, criteria, expected_count):
    """Helper function used in finding matching activity stream elements.
    :param elements: list of activity stream elements.
    :param criteria: dictionary used in finding matching activity stream elements.
    :expected_count: expected number of matching activity stream elements.
    """
    # find number of matching activity stream elements
    count = 0
    for element in elements:
        if all(item in element.json.items() for item in criteria.items()):
            count += 1
    # assert correct amount of matching activity stream elements
    assert count == expected_count, \
        "Expected {0} matching activity stream elements to be found but found {1}.\nUsed the following as criteria:\n{2}\n\n"\
        "Looked through these elements:\n{3}".format(expected_count, count, criteria, elements)


@pytest.fixture
def modify_settings(api_settings_all_pg, update_setting_pg):
    """Helper fixture used for changing Tower settings."""
    def func():
        """Change one setting under each nested /api/v2/settings/ endpoint. The setting selected
        must not change the system in a manner that will interfere with tests.

        Example: disabiling "AUTH_BASIC_ENABLED" will cause Tower to reject all subsequent REST
        requests.
        """
        # update Tower settings
        payload = dict(SESSION_COOKIE_AGE=100000,  # /api/v2/settings/authentication/
                       SOCIAL_AUTH_AZUREAD_OAUTH2_KEY="test",  # /api/v2/settings/azuread-oauth2/
                       SOCIAL_AUTH_GITHUB_KEY="test",  # /api/v2/settings/settings/github/
                       SOCIAL_AUTH_GITHUB_ORG_KEY="test",  # /api/v2/settings/settings/github-org/
                       SOCIAL_AUTH_GITHUB_TEAM_KEY="test",  # /api/v2/settings/settings/github-team/
                       SOCIAL_AUTH_GOOGLE_OAUTH2_KEY="test",  # /api/v2/settings/google-oauth2/
                       SCHEDULE_MAX_JOBS=30,  # /api/v2/settings/jobs/
                       AUTH_LDAP_START_TLS=True,  # /api/v2/settings/ldap/
                       LOG_AGGREGATOR_USERNAME="test",  # /api/v2/settings/logging/
                       RADIUS_PORT=1000,  # /api/v2/settings/radius/
                       SOCIAL_AUTH_SAML_SP_ENTITY_ID="test",  # /api/v2/settings/saml/
                       ACTIVITY_STREAM_ENABLED=False, # /api/v2/settings/system/
                       TACACSPLUS_PORT=777,  # /api/v2/settings/tacasplus/
                       CUSTOM_LOGIN_INFO="test")  # /api/v2/settings/ui/
        update_setting_pg(api_settings_all_pg, payload)
        return payload
    return func


@pytest.fixture
def modify_obfuscated_settings(api_settings_all_pg, update_setting_pg, unencrypted_rsa_ssh_key_data):
    """Helper fixture used for changing Tower settings."""
    def func():
        """Change all settings that need to get obfuscated by the API. The setting selected
        must not change the system in a manner that will interfere with tests.

        Example: disabiling "AUTH_BASIC_ENABLED" will cause Tower to reject all subsequent REST
        requests.
        """
        # update Tower settings
        required_plaintext_fields = ['TACACSPLUS_HOST']
        payload = dict(SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET="test",  # /api/v2/settings/azuread-oauth2/
                       SOCIAL_AUTH_GITHUB_SECRET="test",  # /api/v2/settings/github/
                       SOCIAL_AUTH_GITHUB_ORG_SECRET="test",  # /api/v2/settings/github-org/
                       SOCIAL_AUTH_GITHUB_TEAM_SECRET="test",  # /api/v2/settings/github-team/
                       SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET="test",  # /api/v2/settings/google-oauth2//
                       AUTH_LDAP_BIND_PASSWORD="test",  # /api/v2/settings/ldap/
                       LOG_AGGREGATOR_PASSWORD="test",  # /api/v2/settings/logging/
                       RADIUS_SECRET="test",  # /api/v2/settings/radius/
                       SOCIAL_AUTH_SAML_SP_PRIVATE_KEY=unencrypted_rsa_ssh_key_data,  # /api/v2/settings/saml/
                       TACACSPLUS_HOST="test",  # /api/v2/settings/tacasplus/ (required by TACACSPLUS_SECRET)
                       TACACSPLUS_SECRET="test")  # /api/v2/settings/tacasplus/
        update_setting_pg(api_settings_all_pg, payload)
        return payload, required_plaintext_fields
    return func


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken')
class TestGeneralSettings(APITest):

    def test_included_modules(self, host, ssh_credential, api_ad_hoc_commands_pg, ad_hoc_module_name_choices,
                              api_settings_jobs_pg, update_setting_pg):
        """Verifies that adding additional modules to AD_HOC_COMMANDS unlocks additional modules."""
        # update allowed commands
        payload = dict(AD_HOC_COMMANDS=['shell'])
        update_setting_pg(api_settings_jobs_pg, payload)

        # assess options choices
        assert ad_hoc_module_name_choices() == [['shell', 'shell']], \
            "Ad hoc command OPTIONS not updated for updated AD_HOC_COMMANDS."

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="shell",
                       module_args="true", )

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed().assert_successful()

        # check that correct module run
        assert command_pg.module_name == "shell", "Incorrect module run. Expected 'shell' but got %s." % command_pg.module_name

    def test_excluded_modules(self, inventory, ssh_credential, api_ad_hoc_commands_pg, ad_hoc_module_name_choices,
                              api_settings_jobs_pg, update_setting_pg):
        """Verifies that removed modules from AD_HOC_COMMANDS are no longer callable."""
        # update allowed commands
        payload = dict(AD_HOC_COMMANDS=[])
        update_setting_pg(api_settings_jobs_pg, payload)

        # assess options choices
        assert ad_hoc_module_name_choices() == [], \
            "Ad hoc command OPTIONS not updated for updated AD_HOC_COMMANDS."

        module_names = ['command',
                        'shell',
                        fauxfactory.gen_utf8(),
                        fauxfactory.gen_alphanumeric(),
                        fauxfactory.gen_positive_integer()]

        # create payload
        for module_name in module_names:
            payload = dict(inventory=inventory.id,
                           credential=ssh_credential.id,
                           module_name=module_name,
                           module_args="true", )

            # post the command
            exc_info = pytest.raises(exc.BadRequest, api_ad_hoc_commands_pg.post, payload)
            result = exc_info.value[1]

            # assess result
            assert result == {'module_name': ['"%s" is not a valid choice.' % module_name]}, \
                "Unexpected response upon launching ad hoc command %s not included in AD_HOC_COMMANDS: %s." \
                % (module_name, json.dumps(result))

    def test_relaunch_with_excluded_module(self, ad_hoc_with_status_completed, api_settings_jobs_pg, update_setting_pg):
        """Verifies that you cannot relaunch a command which has been removed from AD_HOC_COMMANDS."""
        # update allowed commands
        payload = dict(AD_HOC_COMMANDS=[])
        update_setting_pg(api_settings_jobs_pg, payload)

        relaunch_pg = ad_hoc_with_status_completed.get_related('relaunch')

        # relaunch ad hoc command
        exc_info = pytest.raises(exc.BadRequest, relaunch_pg.post)
        result = exc_info.value[1]

        # assess result
        assert result == {'module_name': ['"ping" is not a valid choice.']}, \
            "Unexpected response when relaunching ad hoc command whose module " \
            "has been removed from AD_HOC_COMMANDS: %s." % json.dumps(result)

    def test_stdout_max_bytes_display(self, unified_job_with_stdout, api_settings_jobs_pg, update_setting_pg):
        """Assert that all of our unified jobs include stdout by default. Then assert that
        stdout gets truncated once 'STDOUT_MAX_BYTES_DISPLAY' gets set to zero. We check
        both uj.result_stdout and uj.related.stdout here.
        """
        # Value should be the default, but set in case it began as another value
        payload = dict(STDOUT_MAX_BYTES_DISPLAY=1048576)
        update_setting_pg(api_settings_jobs_pg, payload)

        # check that by default that our unified job includes result_stdout
        assert unified_job_with_stdout.result_stdout, \
            "Unified job did not include result_stdout - %s." % unified_job_with_stdout
        # check that by default that our unified job related stdout not censored
        # note: system jobs do not have a related stdout endpoint
        if unified_job_with_stdout.type != "system_job":
            assert "Standard Output too large to display" not in unified_job_with_stdout.connection.get(unified_job_with_stdout.related.stdout).text, \
                "UJ related stdout unexpectedly censored - %s." % unified_job_with_stdout

        # update stdout max bytes flag
        payload = dict(STDOUT_MAX_BYTES_DISPLAY=0)
        update_setting_pg(api_settings_jobs_pg, payload)

        # assert new job stdout truncated
        if unified_job_with_stdout.type == "system_job":
            stdout_page = unified_job_with_stdout.get()['result_stdout']
        else:
            stdout_page = unified_job_with_stdout.connection.get(
                unified_job_with_stdout.related.stdout, query_parameters={'format': 'json'}
            ).json()['content']
        assert re.search(r'^Standard Output too large to display \(\d+ bytes\), only download supported for sizes over 0 bytes.$',
                         stdout_page), \
            "Expected result_stdout error message not matched - %s." % stdout_page
        if unified_job_with_stdout.type != "system_job":
            assert "Standard Output too large to display" in unified_job_with_stdout.connection.get(unified_job_with_stdout.related.stdout).text, \
                "UJ related stdout censorship notice not displayed."

    @pytest.mark.skip(reason="Test flakiness detailed here: https://github.com/ansible/tower-qa/issues/882")
    def test_schedule_max_jobs(self, request, factories, api_settings_jobs_pg, update_setting_pg):
        """Verifies that number of spawned schedule jobs is capped by SCHEDULE_MAX_JOBS.

        Note: SCHEDULE_MAX_JOBS caps the number of waiting scheduled jobs spawned by
        the schedules of a JT. In this test, since we create three schedules, one job
        will start running immediately and only one should be waiting even though we
        have three schedules.
        """
        job_template = factories.job_template()

        # update max schedules flag
        payload = dict(SCHEDULE_MAX_JOBS=1)
        update_setting_pg(api_settings_jobs_pg, payload)

        # create three schedules
        schedules = []
        schedules_pg = job_template.get_related('schedules')
        for _ in range(3):
            payload = dict(name="Schedule - %s" % fauxfactory.gen_utf8(),
                           rrule="DTSTART:20160926T040000Z RRULE:FREQ=MINUTELY;INTERVAL=1")
            schedule_pg = schedules_pg.post(payload)
            schedules.append(schedule_pg)

        # wait for scheduled jobs to spawn and assert that only two jobs spawned
        # Note: since our schedules spawn jobs minutely, we should only have one set of
        # spawned jobs within our timeout window
        jobs = job_template.get_related('jobs')

        try:
            poll_until(lambda: getattr(jobs.get(), 'count') == 2, interval=5, timeout=90)
        except exc.WaitUntilTimeout:
            pytest.fail("unable to verify the expected number of jobs (2)")

        # wait for jobs to finish for clean test teardown
        for job in jobs.results:
            job.wait_until_completed()

    def test_schedule_max_jobs_workflow_level(self, factories, api_settings_jobs_pg, update_setting_pg):
        host = factories.host()
        jt = factories.job_template(
            inventory=host.ds.inventory, playbook='sleep.yml', extra_vars='{"sleep_interval": 120}'
        )
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        payload = dict(SCHEDULE_MAX_JOBS=1)
        update_setting_pg(api_settings_jobs_pg, payload)

        schedules_pg = wfjt.get_related('schedules')
        payload = dict(
            name="Schedule - %s" % fauxfactory.gen_utf8(),
            rrule="DTSTART:20160926T040000Z RRULE:FREQ=MINUTELY;INTERVAL=1"
        )
        schedules_pg.post(payload)

        wfjobs = wfjt.get_related('workflow_jobs')
        try:
            poll_until(lambda: getattr(wfjobs.get(), 'count') == 2, interval=5, timeout=120)
            assert False, "Workflow JobTemplate does not respect SCHEDULE_MAX_JOBS"
        except exc.WaitUntilTimeout:
            pass

        wfjt.get_related('schedules').results.pop().delete()
        for job in wfjobs.results:
            job.wait_until_completed()

    @pytest.mark.parametrize('timeout, default_job_timeout, status, job_explanation', [
        (0, 1, 'failed', 'Job terminated due to timeout'),
        (60, 1, 'successful', ''),
        (-1, 1, 'successful', ''),
    ], ids=['without JT timeout - with global timeout',
            'with JT timeout - with global timeout',
            'with negative JT timeout - with global timeout'])
    def test_default_job_timeout(self, factories, api_settings_jobs_pg, update_setting_pg, timeout, default_job_timeout,
                                 status, job_explanation):
        """Tests DEFAULT_JOB_TIMEOUT. JT timeout value should override DEFAULT_JOB_TIMEOUT
        in instances where both timeout values are supplied.
        """
        job_template = factories.job_template(timeout=timeout, playbook='sleep.yml', extra_vars='sleep_interval: 10')
        factories.host(inventory=job_template.ds.inventory)

        # update job timeout flag
        payload = dict(DEFAULT_JOB_TIMEOUT=default_job_timeout)
        update_setting_pg(api_settings_jobs_pg, payload)

        # launch JT and assess spawned job
        job_pg = job_template.launch().wait_until_completed()
        assert job_pg.status == status, \
            "Unexpected job status. Expected '{0}' but received '{1}.'".format(status, job_pg.status)
        assert job_pg.job_explanation == job_explanation, \
            "Unexpected job job_explanation. Expected '{0}' but received '{1}.'".format(job_explanation, job_pg.job_explanation)
        assert job_pg.timeout == job_template.timeout, \
            "Job_pg has a different timeout value ({0}) than its JT ({1}).".format(job_pg.timeout, job_template.timeout)

    @pytest.mark.parametrize('timeout, default_update_timeout, status, job_explanation', [
        (0, 1, 'failed', 'Job terminated due to timeout'),
        (60, 1, 'successful', ''),
        (-1, 1, 'successful', ''),
    ], ids=['without inv_source timeout - with global timeout',
            'with inv_source timeout - with global timeout',
            'with negative inv_source timeout - with global timeout'])
    def test_default_inventory_update_timeout(self, custom_inventory_source, api_settings_jobs_pg, update_setting_pg, timeout, default_update_timeout,
                                              status, job_explanation):
        """Tests DEFAULT_INVENTORY_UPDATE_TIMEOUT. Inventory source timeout value should override
        DEFAULT_INVENTORY_SOURCE_TIMEOUT in instances where both timeout values are supplied.
        """
        custom_inventory_source.patch(timeout=timeout)

        # update job timeout flag
        payload = dict(DEFAULT_INVENTORY_UPDATE_TIMEOUT=default_update_timeout)
        update_setting_pg(api_settings_jobs_pg, payload)

        # launch inventory update and assess spawned update
        update_pg = custom_inventory_source.update().wait_until_completed()
        assert update_pg.status == status, \
            "Unexpected inventory update status. Expected '{0}' but received '{1}.'".format(status, update_pg.status)
        assert update_pg.job_explanation == job_explanation, \
            "Unexpected update job_explanation. Expected '{0}' but received '{1}.'".format(job_explanation, update_pg.job_explanation)
        assert update_pg.timeout == custom_inventory_source.timeout, \
            "Update_pg has a different timeout value ({0}) than its inv_source ({1}).".format(update_pg.timeout, custom_inventory_source.timeout)

    @pytest.mark.parametrize('timeout, default_update_timeout, status, job_explanation', [
        (0, 1, 'failed', 'Job terminated due to timeout'),
        (60, 1, 'successful', ''),
        (-1, 1, 'successful', ''),
    ], ids=['without project timeout - with global timeout',
            'with project timeout - with global timeout',
            'with negative project timeout - with global timeout'])
    def test_default_project_update_with_timeout(self, project, api_settings_jobs_pg, update_setting_pg, timeout, default_update_timeout,
                                                 status, job_explanation):
        """Tests DEFAULT_PROJECT_UPDATE_TIMEOUT. Project timeout value should override
        DEFAULT_PROJECT_UPDATE_TIMEOUT in instances where both timeout values are supplied.
        """
        project.patch(timeout=timeout)

        # update job timeout flag
        payload = dict(DEFAULT_PROJECT_UPDATE_TIMEOUT=default_update_timeout)
        update_setting_pg(api_settings_jobs_pg, payload)

        # launch project update and assess spawned update
        update_pg = project.update().wait_until_completed()
        assert update_pg.status == status, \
            "Unexpected project update status. Expected '{0}' but received '{1}.'".format(status, update_pg.status)
        assert update_pg.job_explanation == job_explanation, \
            "Unexpected update job_explanation. Expected '{0}' but received '{1}.'".format(job_explanation, update_pg.job_explanation)
        assert update_pg.timeout == project.timeout, \
            "Update_pg has a different timeout value ({0}) than its project ({1}).".format(update_pg.timeout, project.timeout)

    @pytest.mark.parametrize('timeout, status', [
        (1, 'failed'),
        (60, 'successful'),
    ], ids=['timeout executed', 'timeout not executed'])
    def test_ansible_fact_cache_timeout(self, factories, api_settings_jobs_pg, update_setting_pg, timeout, status):
        # update job timeout flag
        payload = dict(ANSIBLE_FACT_CACHE_TIMEOUT=timeout)
        update_setting_pg(api_settings_jobs_pg, payload)

        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='gather_facts.yml', use_fact_cache=True)
        jt.launch().wait_until_completed().assert_successful()

        jt.patch(playbook='use_facts.yml', job_tags='ansible_facts')
        job = jt.launch().wait_until_completed()
        assert job.status == status

        if status == "successful":
            ansible_facts = host.related.ansible_facts.get()
            assert ansible_facts.ansible_distribution in job.result_stdout
            assert ansible_facts.ansible_machine in job.result_stdout
            assert ansible_facts.ansible_system in job.result_stdout
        else:
            assert "The error was: 'ansible_distribution' is undefined" in job.result_stdout

    def test_primary_galaxy_validation_need_url(self, api_settings_jobs_pg, update_setting_pg):
        """Several of these settings have mutual-exclusivity conditions in Ansible core settings
        This tests that the exclusivity rules are enforced on the Tower side"""
        payload = dict(
            PRIMARY_GALAXY_URL='',
            PRIMARY_GALAXY_USERNAME='admin',
            PRIMARY_GALAXY_PASSWORD='g4lxZforU'
        )
        with pytest.raises(exc.BadRequest) as excinfo:
            update_setting_pg(api_settings_jobs_pg, payload)
        for key in ('PRIMARY_GALAXY_USERNAME', 'PRIMARY_GALAXY_PASSWORD'):
            assert key in excinfo.value.msg
            assert excinfo.value.msg[key][0] == 'Cannot provide field if PRIMARY_GALAXY_URL is not set.'

    def test_primary_galaxy_validation_token_vs_password(self, api_settings_jobs_pg, update_setting_pg, skip_if_pre_ansible29):
        payload = dict(
            PRIMARY_GALAXY_URL='https://foo.invalid',
            PRIMARY_GALAXY_USERNAME='admin',
            PRIMARY_GALAXY_PASSWORD='g4lxZforU',
            PRIMARY_GALAXY_TOKEN='g4lxZforMe',
            PRIMARY_GALAXY_AUTH_URL='https://foo.invalid'
        )
        with pytest.raises(exc.BadRequest) as excinfo:
            update_setting_pg(api_settings_jobs_pg, payload)
        for key in ('PRIMARY_GALAXY_TOKEN', 'PRIMARY_GALAXY_PASSWORD'):
            assert key in excinfo.value.msg
            assert excinfo.value.msg[key][0] == ('Setting Galaxy token and authentication URL is '
                                                 'mutually exclusive with username and password.')

    def test_primary_galaxy_exclusivity_rules(self, api_settings_jobs_pg, update_setting_pg, skip_if_pre_ansible29):
        payload = dict(
            PRIMARY_GALAXY_URL='https://foo.invalid',
            PRIMARY_GALAXY_USERNAME='admin',
            PRIMARY_GALAXY_PASSWORD=''
        )
        with pytest.raises(exc.BadRequest) as excinfo:
            update_setting_pg(api_settings_jobs_pg, payload)
        for key in ('PRIMARY_GALAXY_USERNAME', 'PRIMARY_GALAXY_PASSWORD'):
            assert key in excinfo.value.msg
            assert excinfo.value.msg[key][0] == ('If authenticating via username and password, both must be provided.')
        payload = dict(
            PRIMARY_GALAXY_URL='https://foo.invalid',
            PRIMARY_GALAXY_TOKEN='',
            PRIMARY_GALAXY_AUTH_URL='https://foo.invalid'
        )
        with pytest.raises(exc.BadRequest) as excinfo:
            update_setting_pg(api_settings_jobs_pg, payload)
        for key in ('PRIMARY_GALAXY_TOKEN', 'PRIMARY_GALAXY_AUTH_URL'):
            assert key in excinfo.value.msg
            assert excinfo.value.msg[key][0] == ('If authenticating via token, both token and authentication URL must be provided.')

    def test_activity_stream_enabled(self, factories, api_activity_stream_pg, api_settings_system_pg, update_setting_pg):
        """Verifies that if ACTIVITY_STREAM_ENABLED is enabled that Tower activity gets logged."""
        # find number of current activity stream elements
        old_activity_stream_count = api_activity_stream_pg.get().count

        # enable activity stream
        payload = dict(ACTIVITY_STREAM_ENABLED=True)
        update_setting_pg(api_settings_system_pg, payload)

        # create test organization
        factories.organization()

        # find new activity_stream elements
        generated_elements_count = api_activity_stream_pg.get().count - old_activity_stream_count
        generated_elements = api_activity_stream_pg.get(order_by='-id', page_size=generated_elements_count).results

        # assert specific created elements created
        assert len(generated_elements) == 2, \
            "Unexpected number of created activity stream elements: {0}.".format(len(generated_elements))
        criteria = dict(operation="create", object1="organization", object2="")
        assess_created_elements(generated_elements, criteria, 1)
        criteria = dict(operation="create", object1="setting", object2="")
        assess_created_elements(generated_elements, criteria, 1)

    def test_activity_stream_disabled(self, factories, api_activity_stream_pg, api_settings_system_pg, update_setting_pg):
        """Verifies that if ACTIVITY_STREAM_ENABLED is disabled that future activity is no longer logged."""
        # find number of current activity stream elements
        old_activity_stream_count = api_activity_stream_pg.get().count

        # disable activity stream
        payload = dict(ACTIVITY_STREAM_ENABLED=False)
        update_setting_pg(api_settings_system_pg, payload)

        # create test organization
        factories.organization()

        # assert that no activity stream elements created
        new_activity_stream_count = api_activity_stream_pg.get().count
        assert old_activity_stream_count == new_activity_stream_count, \
            "New activity stream entry[ies] found after creating test organization with ACTIVITY_STREAM_ENABLED disabled."

    def test_activity_stream_enabled_for_inventory_sync(self, factories, custom_inventory_source, api_activity_stream_pg,
                                                        api_settings_system_pg, update_setting_pg):
        """Verifies that if ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC is enabled that:
        * inventory update group/host creation gets logged
        * group/host role association gets logged
        * other Tower operations still get logged
        """
        # find number of current activity stream elements
        old_activity_stream_count = api_activity_stream_pg.get().count

        # enable activity stream for inventory updates
        payload = dict(ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC=True)
        update_setting_pg(api_settings_system_pg, payload)

        # create test organization
        factories.organization()

        # launch inventoy update
        custom_inventory_source.update().wait_until_completed()

        # find new activity_stream elements
        generated_elements_count = api_activity_stream_pg.get().count - old_activity_stream_count
        generated_elements = api_activity_stream_pg.get(order_by='-id', page_size=generated_elements_count).results

        # assert specific created elements created
        assert len(generated_elements) == 13, \
            "Unexpected number of created activity stream elements: {0}.".format(len(generated_elements))
        criteria = dict(operation="create", object1="host", object2="")
        assess_created_elements(generated_elements, criteria, 5)
        criteria = dict(operation="create", object1="group", object2="")
        assess_created_elements(generated_elements, criteria, 1)
        criteria = dict(operation="create", object1="organization", object2="")
        assess_created_elements(generated_elements, criteria, 1)
        criteria = dict(operation="create", object1="setting", object2="")
        assess_created_elements(generated_elements, criteria, 1)

        criteria = dict(operation="associate", object1="group", object2="host")
        assess_created_elements(generated_elements, criteria, 5)

    def test_activity_stream_disabled_for_inventory_sync(self, factories, custom_inventory_source, api_activity_stream_pg,
                                                         api_settings_system_pg, update_setting_pg):
        """Verifies that if ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC is disabled that:
        * inventory update group/host creation does not get logged
        * group/host role association does not get logged
        * other Tower operations still get logged
        """
        # find number of current activity stream elements
        old_activity_stream_count = api_activity_stream_pg.get().count

        # disable activity stream for inventory updates
        payload = dict(ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC=False)
        update_setting_pg(api_settings_system_pg, payload)

        # create test organization
        factories.organization()

        # launch inventoy update
        custom_inventory_source.update().wait_until_completed()

        # find new activity_stream elements
        generated_elements_count = api_activity_stream_pg.get().count - old_activity_stream_count
        generated_elements = api_activity_stream_pg.get(order_by='-id', page_size=generated_elements_count).results

        # assert specific created elements created
        assert len(generated_elements) == 2, \
            "Unexpected number of created activity stream elements: {0}.".format(len(generated_elements))
        criteria = dict(operation="create", object1="organization", object2="")
        assess_created_elements(generated_elements, criteria, 1)
        criteria = dict(operation="create", object1="setting", object2="")
        assess_created_elements(generated_elements, criteria, 1)

    def test_org_admins_can_see_all_users(self, org_users, non_org_users, org_admin, api_users_pg,
                                          api_settings_system_pg, update_setting_pg):
        """Tests that when ORG_ADMINS_CAN_SEE_ALL_USERS is enabled that org_admins can see all users systemwide."""
        # enable org_admins from seeing all users
        payload = dict(ORG_ADMINS_CAN_SEE_ALL_USERS=True)
        update_setting_pg(api_settings_system_pg, payload)

        with self.current_user(org_admin):
            # find users within current organization
            matching_org_users = api_users_pg.get(username__in=','.join([u.username for u in org_users]))

            # assert user visibility
            assert matching_org_users.count == len(org_users), \
                "An org_admin is unable to see users (%s) within the same organization." % matching_org_users.count

            # find users outside current organization
            matching_non_org_users = api_users_pg.get(username__in=','.join([u.username for u in non_org_users]))

            # assert user visibility
            assert matching_non_org_users.count == len(non_org_users), \
                "An Org Admin is unable to see users (%s) outside the organization, despite the default setting " \
                "ORG_ADMINS_CAN_SEE_ALL_USERS:True" % matching_non_org_users.count

    def test_org_admins_can_see_all_teams(self, factories, org_admin,
                                          api_settings_system_pg, update_setting_pg):
        """ORG_ADMINS_CAN_SEE_ALL_USERS also allows viewing all teams."""
        # NOTE: the default setting value is True
        payload = dict(ORG_ADMINS_CAN_SEE_ALL_USERS=False)
        update_setting_pg(api_settings_system_pg, payload)

        other_org_team = factories.team()

        # Without setting on, org_admin can not see other org teams
        with self.current_user(org_admin):
            with pytest.raises(exc.Forbidden):
                other_org_team.get()

        payload = dict(ORG_ADMINS_CAN_SEE_ALL_USERS=True)
        update_setting_pg(api_settings_system_pg, payload)

        # With setting on, org_admin can see other teams
        with self.current_user(org_admin):
            other_org_team.get()

    def test_org_admins_cannot_see_all_users(self, org_users, non_org_users, org_admin, api_users_pg, user_password,
                                             api_settings_system_pg, update_setting_pg):
        """Tests that when ORG_ADMINS_CAN_SEE_ALL_USERS is disabled that org_admins can only see users within
        their own organization.
        """
        # disable org_admins from seeing all users
        payload = dict(ORG_ADMINS_CAN_SEE_ALL_USERS=False)
        update_setting_pg(api_settings_system_pg, payload)

        with self.current_user(username=org_admin.username, password=user_password):
            # find users within current organization
            matching_org_users = api_users_pg.get(username__in=','.join([u.username for u in org_users]))

            # assert user visibility
            assert matching_org_users.count == len(org_users), \
                "An org_admin is unable to see users (%s) within the same organization." % matching_org_users.count

            # find users outside current organization
            matching_non_org_users = api_users_pg.get(username__in=','.join([u.username for u in non_org_users]))

            # assert user visibility
            assert matching_non_org_users.count == 0, \
                "An org_admin is able to see users (%s) outside the organization, despite the setting " \
                "ORG_ADMINS_CAN_SEE_ALL_USERS:False" % matching_non_org_users.count

    def test_reset_setting(self, setting_pg, modify_settings):
        """Verifies that settings get restored to factory defaults with a DELETE request."""
        # store initial endpoint JSON
        initial_json = setting_pg.get().json

        # update settings and check for changes
        payload = modify_settings()
        updated_json = setting_pg.get().json
        assert any([item in updated_json.items() for item in payload.items()]), \
            "No changed entry found under {0}.".format(setting_pg.endpoint)
        assert initial_json != updated_json, \
            "Expected {0} to look different after changing Tower settings.\n\nJSON before:\n{1}\n\nJSON after:\n{2}\n".format(
                setting_pg.endpoint, initial_json, updated_json)

        # reset nested settings endpoint and check that defaults restored
        setting_pg.delete()
        assert initial_json == setting_pg.get().json, \
            "Expected {0} to be reverted to initial state after submitting DELETE request.\n\nJSON before:\n{1}\n\nJSON after:\n{2}\n".format(
                setting_pg.endpoint, initial_json, setting_pg.json)

    def test_changed_settings(self, modify_settings, api_settings_changed_pg):
        """Verifies that changed entries show under /api/v2/settings/changed/.
        Note: "TOWER_URL_BASE", "LICENSE" and "INSTALL_UUID" always show here regardless of
        the changes that we make.
        """
        payload = modify_settings()
        settings_changed = api_settings_changed_pg.get()
        optional_read_only_fields = ['AWX_ISOLATED_PRIVATE_KEY', 'AWX_ISOLATED_PUBLIC_KEY']

        # check that all of our updated settings are present under /api/v2/settings/changed/
        assert all([item in settings_changed.json.items() for item in payload.items()]), \
            "Not all changed entries listed under /api/v2/settings/changed/."
        # check for two additional entries under /api/v2/settings/changed/
        assert set(settings_changed.json.keys()) - set(payload.keys()) - set(optional_read_only_fields) == \
            set(['TOWER_URL_BASE', 'INSTALL_UUID', 'LICENSE']), "Unexpected additional items listed under /api/v2/settings/changed/."

    def test_setting_obfuscation(self, api_settings_pg, modify_obfuscated_settings):
        """Verifies that sensitive setting values get obfuscated."""
        payload, required_plaintext_fields = modify_obfuscated_settings()

        # check that all nested settings endpoints have sensitive values obfuscated
        api_settings_pg.get()
        for endpoint in api_settings_pg.results:
            endpoint.get()
            relevant_keys = [key for key in endpoint.json.keys() if key in payload and key in endpoint.json]
            for key in relevant_keys:
                if key in required_plaintext_fields:
                    continue
                assert endpoint.json[key] == "$encrypted$", \
                    "\"{0}\" not obfuscated in {1}.".format(key, endpoint.endpoint)

    def test_job_settings_awx_task_env_var_in_unified_job_env(self, request, api_settings_pg, factories):
        job_settings = api_settings_pg.get_endpoint('jobs')

        original_task_env = job_settings.AWX_TASK_ENV
        request.addfinalizer(lambda: job_settings.patch(AWX_TASK_ENV=original_task_env))

        updated_task_env = original_task_env.copy()
        desired_val = 'some_val'
        updated_task_env['SOME_TEST_ENV_VAR'] = desired_val
        job_settings.AWX_TASK_ENV = updated_task_env

        custom_source = factories.inventory_source(source='custom')
        inv_update = custom_source.update().wait_until_completed()
        inv_update.assert_successful()
        assert inv_update.job_env.SOME_TEST_ENV_VAR == desired_val

        inventory = custom_source.ds.inventory
        host = inventory.related.hosts.get().results[0]

        jt = factories.job_template(inventory=inventory, playbook='ansible_env.yml')
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        assert job.job_env.SOME_TEST_ENV_VAR == desired_val
        debug_event = job.related.job_events.get(task='debug', host=host.id, event__startswith='runner_on_ok').results[0]
        assert debug_event.event_data.res.ansible_env.SOME_TEST_ENV_VAR == desired_val

        project_update = jt.ds.project.related.project_updates.get().results[0]
        # NOTE: fields like job_env are only present on detail view, and awxkit
        # is not yet designed to auto-fetch these
        project_update = project_update.get()
        assert project_update.job_env.SOME_TEST_ENV_VAR == desired_val

        ahc = factories.ad_hoc_command(inventory=inventory, limit=host.name)
        ahc.wait_until_completed()
        ahc.assert_successful()
        assert ahc.job_env.SOME_TEST_ENV_VAR == desired_val
