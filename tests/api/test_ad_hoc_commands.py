import pytest
import fauxfactory
import json
import qe.exceptions
from tests.api import Base_Api_Test

'''
Tests that span all four endpoints
-[X] Four tests - that super user can GET from all four ad hoc endpoints. Tests will be housed in respective modules.
-[X] Test that POST works for superuser on all four endpoints

Tests for the main api/v1/ad_hoc_commands endpoint
-[X] Verify that privileged users can launch a command from api/v1/ad_hoc_commands
-[X] Verify that unprivileged users cannot launch commands

-[X] Test that posts without specifying module defaults to command
-[X] Test that posts without specifying module_args fails with certain commands
-[X] Verify that cancelling a command works
-[X] Launching with ask-credential (valid passwords, without passwords, with invalid passwords)
-[X] Launching with no limit
-[X] With limit=all
-[X] with limit=$hosts
-[X] with limit=$groups
-[X] with limit=no match
-[] Launching with args => that the args are passed correctly (TODO: discussion church passing args as string/JSON file???)

-[X] Verify that privileged users can relaunch a command
-[X] Verify that unprivileged users cannot relaunch a command
-[X] Verify that command relaunches with deleted related fail
-[X] Verify relaunches with ask credential with both negative and positive cases

Stranger situations
-[X] Simple test: launch a command and assert that the activity stream gets populated
-[X] test changes to settings.py
-[] Launching a command with an invalid payload <= loop through required in options
-[X] Verify that deleting related is reflected correctly in the command page

Permissions
-[X] Verify that unprivileged users cannot launch commands without the ad hoc permission
-[X] Verify that unprivileged users with the correct permissions can launch a command
-[X] Verify that privileged users can launch commands without permissions
'''


@pytest.fixture(scope="function", params=['inventory', 'ssh_credential'])
def deleted_object(request):
    '''
    Creates and deletes an object.
    Returns the deleted object.
    '''
    obj = request.getfuncargvalue(request.param)
    obj.delete()
    return obj


@pytest.fixture(scope="function")
def ad_hoc_command_with_multi_ask_credential_and_password_in_payload(request, host, ssh_credential_multi_ask, api_ad_hoc_commands_pg, testsetup):
    '''
    Launch command with multi_ask credential and passwords in the payload.
    '''
    # create payload
    payload = dict(inventory=host.inventory,
                   credential=ssh_credential_multi_ask.id,
                   module_name="ping",
                   ssh_password=testsetup.credentials['ssh']['password'],
                   ssh_key_unlock=testsetup.credentials['ssh']['encrypted']['ssh_key_unlock'],
                   vault_password=testsetup.credentials['ssh']['vault_password'],
                   become_password=testsetup.credentials['ssh']['become_password'], )

    # post the command
    command_pg = api_ad_hoc_commands_pg.post(payload)

    # assert command successful
    command_pg.wait_until_completed()
    assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

    return command_pg


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Ad_Hoc_Commands_Inventory(Base_Api_Test):
    '''
    From /api/v1/inventories/{id}
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_get_as_superuser(self, inventory):
        '''
        Verify that a superuser account is able to GET from the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = inventory.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    def test_post_as_superuser(self, host, ssh_credential):
        '''
        Verify that a superuser account is able to POST to the ad_hoc_commands endpoint.
        '''
        inventory_pg = host.get_related('inventory')
        ad_hoc_commands_pg = inventory_pg.get_related('ad_hoc_commands')

        # create payload
        payload = dict(inventory=inventory_pg.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload to ad_hoc_commands endpoint
        command_pg = ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Ad_Hoc_Commands_Group(Base_Api_Test):
    '''
    From /api/v1/groups/{id}
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_get_as_superuser(self, group):
        '''
        Verify that a superuser account is able to GET from the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = group.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    def test_post_as_superuser(self, group, host, ssh_credential):
        '''
        Verify that a superuser account is able to POST to the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = group.get_related('ad_hoc_commands')

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post the command
        command_pg = ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Ad_Hoc_Commands_Host(Base_Api_Test):
    '''
    From /api/v1/hosts/{id}/
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_get_as_superuser(self, host):
        '''
        Verify that a superuser account is able to GET from the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = host.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    def test_post_as_superuser(self, host, ssh_credential):
        '''
        Verify that a superuser account is able to POST to the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = host.get_related('ad_hoc_commands')

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post the command
        command_pg = ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Ad_Hoc_Commands_Main(Base_Api_Test):
    '''
    For the api/v1/ad_hoc_commands endpoint.
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_get(self, api_ad_hoc_commands_pg, all_users, user_password):
        '''
        Verify that privileged users are able to GET from the ad_hoc_commands endpoint.
        '''
        for user in all_users:
            with self.current_user(user.username, user_password):
                api_ad_hoc_commands_pg.get()

    def test_post_as_privileged_user(self, host, ssh_credential, api_ad_hoc_commands_pg, privileged_users, user_password):
        '''
        Verify that a superuser account is able to post to the ad_hoc_commands endpoint.
        '''
        use_role_pg = ssh_credential.get_object_role('use_role')

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as privileged user
        for privileged_user in privileged_users:
            # give privileged user 'use_role' permissions
            with pytest.raises(qe.exceptions.NoContent_Exception):
                use_role_pg.get_related('users').post(dict(id=privileged_user.id))
            with self.current_user(privileged_user.username, user_password):
                command_pg = api_ad_hoc_commands_pg.post(payload)

                # assert command successful
                command_pg.wait_until_completed()
                assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

    def test_post_as_unprivileged_user(self, inventory, ssh_credential, api_ad_hoc_commands_pg, unprivileged_users, user_password):
        '''
        Verify that unprivileged users cannot post to the ad_hoc_commands endpoint.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as unprivileged user
        for unprivileged_user in unprivileged_users:
            ssh_credential.patch(user=unprivileged_user.id)
            with self.current_user(unprivileged_user.username, user_password):
                with pytest.raises(qe.exceptions.Forbidden_Exception):
                    api_ad_hoc_commands_pg.post(payload)

    def test_launch_without_module_name(self, host, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Verifies that if you post without specifiying module_name that the command module is run.
        '''
        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_args="true", )

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

        # check that command was indeed of module "command"
        assert command_pg.module_name == "command"
        assert command_pg.module_args == "true"

    def test_launch_with_invalid_module_name(self, inventory, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Verifies that if you post with an invalid module_name that a BadRequest exception is raised.
        '''
        invalid_module_names = [-1, 0, 1, True, False, (), {}]

        for invalid_module_name in invalid_module_names:
            # create payload
            payload = dict(inventory=inventory.id,
                           credential=ssh_credential.id,
                           module_name=invalid_module_name, )

            # post the command
            with pytest.raises(qe.exceptions.BadRequest_Exception):
                api_ad_hoc_commands_pg.post(payload)

    def test_launch_without_module_args(self, inventory, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Verifies that if you post without specifiying module_args that the post fails with
        the command module.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="command", )

        # post the command
        exc_info = pytest.raises(qe.exceptions.BadRequest_Exception, api_ad_hoc_commands_pg.post, payload)
        result = exc_info.value[1]

        # assess result
        assert result == {u'module_args': [u'No argument passed to command module.']}, \
            "Unexpected response upon launching ad hoc command 'command' without " \
            "specifying module_args. %s" % json.dumps(result)

    @pytest.mark.fixture_args(module_name='command', module_args='sleep 60s')
    def test_cancel_command(self, ad_hoc_with_status_pending):
        '''
        Tests that posting to the cancel endpoint cancels a command.
        '''
        cancel_pg = ad_hoc_with_status_pending.get_related('cancel')

        # verify that you can cancel
        assert cancel_pg.can_cancel, "Unable to cancel command (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel the command
        cancel_pg.post()

        # verify that the command was canceled
        ad_hoc_with_status_pending.wait_until_completed()
        assert ad_hoc_with_status_pending.status == 'canceled', \
            "Unexpected command status after cancelling (expected " \
            "status:canceled) - %s" % ad_hoc_with_status_pending

    def test_launch_with_ask_credential_and_passwords_in_payload(self, host, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
        '''
        Verifies that launching a command with an ask credential succeeds when supplied with proper passwords.
        '''
        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential_multi_ask.id,
                       module_name="ping",
                       ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       vault_password=self.credentials['ssh']['vault_password'],
                       become_password=self.credentials['ssh']['become_password'], )

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s" % command_pg

    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, inventory, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
        '''
        Verifies that launching a command with an ask credential fails when not supplied with required passwords.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential_multi_ask.id,
                       module_name="ping", )

        # post the command
        with pytest.raises(qe.exceptions.BadRequest_Exception):
            api_ad_hoc_commands_pg.post(payload)

    def test_launch_with_ask_credential_and_invalid_passwords_in_payload(self, inventory, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
        '''
        Verifies that launching a command with an ask credential fails when supplied with invalid passwords.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential_multi_ask.id,
                       module_name="ping",
                       ssh_password=fauxfactory.gen_utf8(),
                       ssh_key_unlock=fauxfactory.gen_utf8(),
                       vault_password=fauxfactory.gen_utf8(),
                       become_password=fauxfactory.gen_utf8())

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert success
        command_pg.wait_until_completed()
        assert not command_pg.is_successful, "Command successful, but was expected to fail - %s " % command_pg

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3544')
    @pytest.mark.parametrize("limit_value, expected_count", [
        ("", 11),
        ("all", 11),
        ("host-6", 1),
        ("group-1", 4),
        ("group*:&group-1:!duplicate_host", 3),  # All groups intersect with "group-1" and not "duplicate_host"
        ("duplicate_host", 1),
    ])
    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import json

# Create hosts and groups
inv = dict(_meta=dict(hostvars={}), hosts=[])
inv['group-0'] = [
   "duplicate_host",
   "host with spaces in name",
   "host-1",
   "host-2",
   "host-3",
]
inv['group-1'] = [
   "duplicate_host",
   "host-4",
   "host-5",
   "host-6",
]
inv['group-2'] = [
   "duplicate_host",
   "host-7",
   "host-8",
   "host-9",
]

# Add _meta hostvars
for grp, hosts in inv.items():
    for host in hosts:
        inv['_meta']['hostvars'][host] = dict(ansible_ssh_host='127.0.0.1', ansible_connection='local')

print json.dumps(inv, indent=2)
''')
    def test_launch_with_matched_limit_value(
            self, limit_value,
            expected_count,
            custom_inventory_update_with_status_completed,
            ssh_credential,
            api_ad_hoc_commands_pg
    ):
        '''
        Verifies that ad hoc command launches with different values for limit behave as expected.
        '''
        # create payload
        payload = dict(inventory=custom_inventory_update_with_status_completed.get_related('inventory_source').inventory,
                       credential=ssh_credential.id,
                       module_name="ping",
                       limit=limit_value)

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload).wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s" % command_pg

        # assert that command run on correct number of hosts
        events_pg = command_pg.get_related('events')
        assert events_pg.count == expected_count

    def test_launch_with_unmatched_limit_value(self, host, ssh_credential, api_ad_hoc_commands_pg, ansible_version_cmp):
        '''
        Verify that launching an ad hoc command without matching host fails appropriately.
        '''
        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="ping",
                       limit=fauxfactory.gen_utf8())

        # check that our limit is unmatched
        hosts_pg = host.get_related('inventory').get_related("hosts")
        host_names = [host.name for host_pg in hosts_pg.results]
        for host_name in host_names:
            assert host_name != payload['limit'], "Matching host unexpectedly found - %s." % host_name

        # launch the job template and check the results
        # unmatched commands fail starting with ansible-2.0.1.0
        job_pg = api_ad_hoc_commands_pg.post(payload).wait_until_completed()
        if ansible_version_cmp('2.0.1.0') < 0:
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
        else:
            assert job_pg.status == "failed", "Unexpected job_pg.status - %s." % job_pg
            assert "--limit does not match any hosts" in job_pg.result_stdout, \
                "Unexpected job_pg.result_stdout when launching an ad hoc command with an unmatched limit."

    def test_relaunch_command_with_privileged_users(
        self, host,
        ssh_credential,
        api_ad_hoc_commands_pg,
        api_unified_jobs_pg,
        privileged_users,
        user_password
    ):
        '''
        Verifies that privileged users can relaunch commands.
        '''
        use_role_pg = ssh_credential.get_object_role('use_role')
        for privileged_user in privileged_users:
            # give privileged user 'use_role' permissions
            with pytest.raises(qe.exceptions.NoContent_Exception):
                use_role_pg.get_related('users').post(dict(id=privileged_user.id))

            # create payload
            payload = dict(inventory=host.inventory,
                           credential=ssh_credential.id,
                           module_name="ping", )

            with self.current_user(privileged_user.username, user_password):
                # post payload to ad_hoc_commands endpoint
                ad_hoc_command_pg = api_ad_hoc_commands_pg.post(payload)

                # verify that the first ad hoc command ran successfully
                ad_hoc_command_pg.wait_until_completed()
                assert ad_hoc_command_pg.is_successful, "Ad hoc command unsuccessful - %s" % ad_hoc_command_pg

                # navigate to relaunch_pg and assert on relaunch_pg value
                relaunch_pg = ad_hoc_command_pg.get_related('relaunch')
                assert not relaunch_pg.passwords_needed_to_start

                # relaunch the job and assert success
                relaunch_pg.post()

                command_pgs = api_unified_jobs_pg.get(id=relaunch_pg.id)
                assert command_pgs.count == 1, \
                    "command relaunched (id:%s) but unable to find matching " \
                    "job." % relaunch_pg.id
                command_pg = command_pgs.results[0]

                command_pg.wait_until_completed()
                assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

    def test_relaunch_command_with_unprivileged_users(self, ad_hoc_with_status_completed, unprivileged_users, user_password):
        '''
        Verifies that unprivileged users cannot relaunch a command originally launched by admin.
        '''
        relaunch_pg = ad_hoc_with_status_completed.get_related('relaunch')

        # relaunch the job and assert success
        for unprivileged_user in unprivileged_users:
            with self.current_user(unprivileged_user.username, user_password):
                with pytest.raises(qe.exceptions.Forbidden_Exception):
                    relaunch_pg.post()

    def test_relaunch_command_with_ask_credential_and_passwords(
        self, request,
        ad_hoc_command_with_multi_ask_credential_and_password_in_payload,
        api_unified_jobs_pg
    ):
        '''
        Tests that command relaunches work when supplied with the right passwords.
        '''
        relaunch_pg = ad_hoc_command_with_multi_ask_credential_and_password_in_payload.get_related('relaunch')

        # create payload
        payload = dict(ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       vault_password=self.credentials['ssh']['vault_password'],
                       become_password=self.credentials['ssh']['become_password'],
                       extra_vars={}, )

        # post to relaunch_pg
        relaunch_pg.post(payload)

        # navigate to command and assert success
        command_pgs = api_unified_jobs_pg.get(id=relaunch_pg.id)
        assert command_pgs.count == 1, \
            "command relaunched (id:%s) but unable to find matching " \
            "job." % relaunch_pg.id
        command_pg = command_pgs.results[0]

        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

    def test_relaunch_command_with_ask_credential_and_without_passwords(
        self, request,
        ad_hoc_command_with_multi_ask_credential_and_password_in_payload,
        api_unified_jobs_pg
    ):
        '''
        Tests that command relaunches fail when supplied without the right passwords.
        '''
        relaunch_pg = ad_hoc_command_with_multi_ask_credential_and_password_in_payload.get_related('relaunch')

        # create payload
        payload = dict(extra_vars={}, )

        # post to relaunch_pg
        with pytest.raises(qe.exceptions.BadRequest_Exception):
            relaunch_pg.post(payload)

    def test_relaunch_with_deleted_related(self, ad_hoc_with_status_completed, deleted_object):
        '''
        Verify that relaunching a job with deleted related fails.
        '''
        # verify that the first ad hoc command ran successfully
        assert ad_hoc_with_status_completed.is_successful, "Ad hoc command unsuccessful - %s" % ad_hoc_with_status_completed

        # navigate to relaunch_pg and assert on relaunch_pg value
        relaunch_pg = ad_hoc_with_status_completed.get_related('relaunch')
        assert not relaunch_pg.passwords_needed_to_start

        # relaunch the command
        with pytest.raises(qe.exceptions.BadRequest_Exception):
            relaunch_pg.post()

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3544')
    @pytest.mark.fixture_args(module_name='shell', module_args='exit 1', job_type='check')
    def test_launch_with_check(self, host, ssh_credential, ad_hoc_with_status_completed):
        '''
        Verifies check command behavior.
        '''
        assert ad_hoc_with_status_completed.is_successful, "Command unsuccessful - %s." % ad_hoc_with_status_completed

        # check command attributes
        assert ad_hoc_with_status_completed.job_type == 'check'
        assert "\"--check\"" in ad_hoc_with_status_completed.job_args, \
            "Launched a check command but '--check' not present in job_args."

        # check that target task skipped
        matching_job_events = ad_hoc_with_status_completed.get_related('events', event='runner_on_skipped')
        assert matching_job_events.count == 1, \
            "Unexpected number of matching job events (%s != 1)" % matching_job_events.count

    def test_ad_hoc_activity_stream(self, api_ad_hoc_commands_pg, ad_hoc_with_status_completed):
        '''
        Verifies that launching an ad hoc command updates the activity stream.
        '''
        # find command and navigate to command page
        ad_hoc_commands_pg = api_ad_hoc_commands_pg.get(id=ad_hoc_with_status_completed.id)
        assert ad_hoc_commands_pg.count == 1, \
            "command launched (id:%s) but unable to find matching " \
            "job." % ad_hoc_with_status_completed.id
        ad_hoc_command_pg = ad_hoc_commands_pg.results[0]

        # verify that activity stream populated after launch
        activity_stream_pg = ad_hoc_command_pg.get_related('activity_stream')
        assert activity_stream_pg.count == 1, "Activity stream not populated."

    def test_command_page_update(self, org_admin, user_password, host, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Tests that deleting related objects will be reflected in the updated command page.
        '''
        use_role_pg = ssh_credential.get_object_role('use_role')
        inventory_pg = host.get_related('inventory')

        # associate ssh_credential with org_admin
        with pytest.raises(qe.exceptions.NoContent_Exception):
            use_role_pg.get_related('users').post(dict(id=org_admin.id))

        # create payload
        payload = dict(inventory=inventory_pg.id,
                       credential=ssh_credential.id,
                       module_name="ping")

        # post payload to ad_hoc_commands endpoint
        with self.current_user(org_admin.username, user_password):
            ad_hoc_command_pg = api_ad_hoc_commands_pg.post(payload)

        # verify that the first ad hoc command ran successfully
        ad_hoc_command_pg.wait_until_completed()
        assert ad_hoc_command_pg.is_successful, "Ad hoc command unsuccessful - %s" % ad_hoc_command_pg

        # delete related objects
        inventory_pg.delete()
        ssh_credential.delete()
        org_admin.delete()

        # verify that properties are updated
        ad_hoc_command_pg.get()
        assert ad_hoc_command_pg.json['inventory'] is None
        assert ad_hoc_command_pg.json['credential'] is None

        # verify that summary fields are updated
        assert "inventory" not in ad_hoc_command_pg.json['summary_fields']
        assert "credential" not in ad_hoc_command_pg.json['summary_fields']
        assert "created_by" not in ad_hoc_command_pg.json['summary_fields']

        # verify that "get_related" updated
        assert "inventory" not in ad_hoc_command_pg.json['related']
        assert "credential" not in ad_hoc_command_pg.json['related']
        assert "created_by" not in ad_hoc_command_pg.json['related']

    @pytest.mark.fixture_args(ad_hoc_commands=['shell'])
    def test_included_modules(self, host, ssh_credential, api_ad_hoc_commands_pg, AD_HOC_COMMANDS, ad_hoc_module_name_choices):
        '''
        Verifies that adding additional modules to ad_hoc.py unlocks additional modules.
        '''
        # assess options choices
        assert ad_hoc_module_name_choices == {u'shell': u'shell'}, \
            "Ad hoc command OPTIONS not updated for updated ad_hoc.py"

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="shell",
                       module_args="true", )

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

        # check that correct module run
        assert command_pg.module_name == "shell", "Incorrect module run. Expected 'shell' but got %s." % command_pg.module_name

    @pytest.mark.fixture_args(ad_hoc_commands=[])
    def test_excluded_modules(self, inventory, ssh_credential, api_ad_hoc_commands_pg, AD_HOC_COMMANDS, ad_hoc_module_name_choices, tower_version_cmp):
        '''
        Verifies that removed modules are no longer callable.
        '''
        # assess options choices
        assert ad_hoc_module_name_choices == {}, \
            "Ad hoc command OPTIONS not updated for updated ad_hoc.py"

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
            exc_info = pytest.raises(qe.exceptions.BadRequest_Exception, api_ad_hoc_commands_pg.post, payload)
            result = exc_info.value[1]

            # assess result
            errorMsg = "Unexpected response upon launching ad hoc command %s not included in " \
                       "ad_hoc.py. %s" % (module_name, json.dumps(result))
            if tower_version_cmp('3.0.0') < 0:
                assert result == {'module_name': ['Select a valid choice. %s is not one of the available choices.' % module_name]}, errorMsg
            else:
                assert result == {u'module_name': [u'"%s" is not a valid choice.' % module_name]}, errorMsg

    @pytest.mark.fixture_args(ad_hoc_commands=[])
    def test_relaunch_with_excluded_module(self, ad_hoc_with_status_completed, api_ad_hoc_commands_pg, AD_HOC_COMMANDS,
                                           tower_version_cmp):
        '''
        Verifies that you cannot relaunch a command which has been removed
        from ad_hoc_commands.py.
        '''
        relaunch_pg = ad_hoc_with_status_completed.get_related('relaunch')

        # relaunch ad hoc command
        exc_info = pytest.raises(qe.exceptions.BadRequest_Exception, relaunch_pg.post)
        result = exc_info.value[1]

        # assess result
        errorMsg = "Unexpected response when relaunching ad hoc command whose module " \
                   "has been removed from ad_hoc.py. %s" % json.dumps(result)
        if tower_version_cmp('3.0.0') < 0:
            assert result == {"module_name": ["Select a valid choice. ping is not one of the available choices."]}, errorMsg
        else:
            assert result == {u'module_name': [u'"ping" is not a valid choice.']}, errorMsg
