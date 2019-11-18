import json

from awxkit import exceptions as exc
from awxkit.config import config
import fauxfactory
import pytest

from tests.api import APITest


@pytest.fixture(scope="function", params=['inventory', 'ssh_credential'])
def deleted_object(request):
    """Creates and deletes an object.
    Returns the deleted object.
    """
    obj = request.getfixturevalue(request.param)
    obj.delete()
    if request.param == 'inventory':
        obj.wait_until_deleted()
    return obj


@pytest.fixture(scope="function")
def ad_hoc_command_with_multi_ask_credential_and_password_in_payload(request, host, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
    """Launch command with multi_ask credential and passwords in the payload."""
    # create payload
    payload = dict(inventory=host.inventory,
                   credential=ssh_credential_multi_ask.id,
                   module_name="ping",
                   ssh_password=config.credentials['ssh']['password'],
                   ssh_key_unlock=config.credentials['ssh']['encrypted']['ssh_key_unlock'],
                   become_password=config.credentials['ssh']['become_password'], )

    # post the command
    command_pg = api_ad_hoc_commands_pg.post(payload)

    # assert command successful
    command_pg.wait_until_completed()
    command_pg.assert_successful()

    return command_pg


@pytest.mark.usefixtures('authtoken')
class Test_Ad_Hoc_Commands_Inventory(APITest):

    def test_get_as_superuser(self, inventory):
        """Verify that a superuser account is able to GET from the ad_hoc_commands endpoint."""
        ad_hoc_commands_pg = inventory.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    @pytest.mark.ansible_integration
    def test_post_as_superuser(self, host, ssh_credential):
        """Verify that a superuser account is able to POST to the ad_hoc_commands endpoint."""
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
        command_pg.assert_successful()


@pytest.mark.usefixtures('authtoken')
class Test_Ad_Hoc_Commands_Group(APITest):

    def test_get_as_superuser(self, group):
        """Verify that a superuser account is able to GET from the ad_hoc_commands endpoint."""
        ad_hoc_commands_pg = group.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    @pytest.mark.ansible_integration
    def test_post_as_superuser(self, group, host, ssh_credential):
        """Verify that a superuser account is able to POST to the ad_hoc_commands endpoint."""
        ad_hoc_commands_pg = group.get_related('ad_hoc_commands')

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post the command
        command_pg = ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        command_pg.assert_successful()


@pytest.mark.usefixtures('authtoken')
class Test_Ad_Hoc_Commands_Host(APITest):

    def test_get_as_superuser(self, host):
        """Verify that a superuser account is able to GET from the ad_hoc_commands endpoint."""
        ad_hoc_commands_pg = host.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    @pytest.mark.ansible_integration
    def test_post_as_superuser(self, host, ssh_credential):
        """Verify that a superuser account is able to POST to the ad_hoc_commands endpoint."""
        ad_hoc_commands_pg = host.get_related('ad_hoc_commands')

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post the command
        command_pg = ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        command_pg.assert_successful()

    def test_host_event_links(self, factories):
        inventory = factories.inventory()
        host = factories.host(name='test_host', inventory=inventory)

        ahc = factories.ad_hoc_command(inventory=inventory).wait_until_completed()
        events = ahc.get_related('events').results
        assert set(event.host for event in events) == set([None, host.id])

        assert set([
            'runner_on_ok', 'runner_on_start', 'playbook_on_stats'
        ]) == set([event['event'] for event in events if event['event'] != 'verbose'])


@pytest.mark.usefixtures('authtoken')
class Test_Ad_Hoc_Commands_Main(APITest):

    def test_get(self, api_ad_hoc_commands_pg, all_users, user_password):
        """Verify that privileged users are able to GET from the ad_hoc_commands endpoint."""
        for user in all_users:
            with self.current_user(user.username, user_password):
                api_ad_hoc_commands_pg.get()

    def test_post_as_privileged_user(self, host, ssh_credential, api_ad_hoc_commands_pg, privileged_users, user_password):
        """Verify that a superuser account is able to post to the ad_hoc_commands endpoint."""
        use_role_pg = ssh_credential.get_object_role('use_role')

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as privileged user
        for privileged_user in privileged_users:
            # give privileged user 'use_role' permissions
            with pytest.raises(exc.NoContent):
                use_role_pg.get_related('users').post(dict(id=privileged_user.id))
            with self.current_user(privileged_user.username, user_password):
                command_pg = api_ad_hoc_commands_pg.post(payload)

                # assert command successful
                command_pg.wait_until_completed()
                command_pg.assert_successful()

    def test_post_as_unprivileged_user(self, inventory, ssh_credential, api_ad_hoc_commands_pg, unprivileged_users, user_password):
        """Verify that unprivileged users cannot post to the ad_hoc_commands endpoint."""
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as unprivileged user
        for unprivileged_user in unprivileged_users:
            ssh_credential.set_object_roles(unprivileged_user, 'admin')
            with self.current_user(unprivileged_user.username, user_password):
                with pytest.raises(exc.Forbidden):
                    api_ad_hoc_commands_pg.post(payload)

    @pytest.mark.ansible_integration
    def test_launch_without_module_name(self, host, ssh_credential, api_ad_hoc_commands_pg):
        """Verifies that if you post without specifiying module_name that the command module is run."""
        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential.id,
                       module_args="true", )

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        command_pg.assert_successful()

        # check that command was indeed of module "command"
        assert command_pg.module_name == "command"
        assert command_pg.module_args == "true"

    @pytest.mark.ansible_integration
    def test_launch_with_credential_plugin(self, v2, k8s_vault, host,
                                           api_ad_hoc_commands_pg, factories,
                                           token=config.credentials.hashivault.token):
        # Hashi Vault Secret Lookup
        cred_type = v2.credential_types.get(
            managed_by_tower=True,
            name='HashiCorp Vault Secret Lookup'
        ).results.pop()
        inputs = {
            'url': k8s_vault,
            'token': token,
            'api_version': 'v1'
        }
        payload = factories.credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type,
            inputs=inputs
        )
        hashi_credential = v2.credentials.post(payload)
        metadata = {
            'secret_path': '/kv/example-user/',
            'secret_key': 'username',
        }

        # Machine Credential Type
        cred_type = v2.credential_types.get(managed_by_tower=True, namespace='ssh').results.pop()
        payload = factories.credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type
        )
        credential = v2.credentials.post(payload)

        # Associating Hashi credential to Machine credential
        credential.related.input_sources.post(dict(
            input_field_name='username',
            source_credential=hashi_credential.id,
            metadata=metadata
        ))

        # create payload
        payload = dict(inventory=host.inventory,
                       credential=credential.id,
                       module_args="true")

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        command_pg.assert_successful()

        # unversionned-username is coming from k8s_vault fixture (/v1/kv/example-user)
        assert 'ansible -u unversioned-username' in command_pg.job_args[-1]

    def test_launch_with_invalid_module_name(self, inventory, ssh_credential, api_ad_hoc_commands_pg):
        """Verifies that if you post with an invalid module_name that a BadRequest exception is raised."""
        invalid_module_names = [-1, 0, 1, True, False, (), {}]

        for invalid_module_name in invalid_module_names:
            # create payload
            payload = dict(inventory=inventory.id,
                           credential=ssh_credential.id,
                           module_name=invalid_module_name, )

            # post the command
            with pytest.raises(exc.BadRequest):
                api_ad_hoc_commands_pg.post(payload)

    def test_launch_without_module_args(self, inventory, ssh_credential, api_ad_hoc_commands_pg):
        """Verifies that if you post without specifiying module_args that the post fails with the command module."""
        # create poad
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="command", )

        # post the command
        exc_info = pytest.raises(exc.BadRequest, api_ad_hoc_commands_pg.post, payload)
        result = exc_info.value[1]

        # assess result
        assert result == {'module_args': ['No argument passed to command module.']}, \
            "Unexpected response upon launching ad hoc command 'command' without " \
            "specifying module_args. %s" % json.dumps(result)

    @pytest.mark.serial
    @pytest.mark.fixture_args(module_name='command', module_args='sleep 60s')
    def test_cancel_command(self, ad_hoc_with_status_pending):
        """Tests that posting to the cancel endpoint cancels a command."""
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

    @pytest.mark.yolo
    @pytest.mark.ansible_integration
    def test_launch_with_ask_credential_and_passwords_in_payload(self, host, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
        """Verifies that launching a command with an ask credential succeeds when supplied with proper passwords."""
        # create payload
        payload = dict(inventory=host.inventory,
                       credential=ssh_credential_multi_ask.id,
                       module_name="ping",
                       ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       become_password=self.credentials['ssh']['become_password'], )

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert command successful
        command_pg.wait_until_completed()
        command_pg.assert_successful()

    @pytest.mark.ansible_integration
    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, inventory, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
        """Verifies that launching a command with an ask credential fails when not supplied with required passwords."""
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential_multi_ask.id,
                       module_name="ping", )

        # post the command
        with pytest.raises(exc.BadRequest):
            api_ad_hoc_commands_pg.post(payload)

    @pytest.mark.ansible_integration
    def test_launch_with_ask_credential_and_invalid_passwords_in_payload(self, inventory, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
        """Verifies that launching a command with an ask credential fails when supplied with invalid passwords."""
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential_multi_ask.id,
                       module_name="ping",
                       ssh_password=fauxfactory.gen_utf8(),
                       ssh_key_unlock=fauxfactory.gen_utf8(),
                       become_password=fauxfactory.gen_utf8())

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload)

        # assert success
        command_pg.wait_until_completed()
        assert not command_pg.is_successful, "Command successful, but was expected to fail - %s " % command_pg

    @pytest.mark.ansible_integration
    @pytest.mark.parametrize("limit_value, expected_count", [
        ("", 11),
        ("all", 11),
        ("host-6", 1),
        ("group-1", 4),
        ("group*:&group-1:!duplicate_host", 3),  # All groups intersect with "group-1" and not "duplicate_host"
        ("duplicate_host", 1),
    ])
    @pytest.mark.fixture_args(source_script="""#!/usr/bin/env python
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
        inv['_meta']['hostvars'][host] = dict(ansible_host='127.0.0.1', ansible_connection='local')

print(json.dumps(inv, indent=2))
""")
    def test_launch_with_matched_limit_value(
            self, limit_value,
            expected_count,
            custom_inventory_update_with_status_completed,
            ssh_credential,
            api_ad_hoc_commands_pg,
            ansible_version_cmp
    ):
        """Verifies that ad hoc command launches with different values for limit behave as expected."""
        # create payload
        payload = dict(inventory=custom_inventory_update_with_status_completed.get_related('inventory_source').inventory,
                       credential=ssh_credential.id,
                       module_name="ping",
                       limit=limit_value)

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload).wait_until_completed()
        command_pg.assert_successful()

        # assert that command run on correct number of hosts
        # TODO(spredzy): Starting with ansible 2.8.0 some times not only `runner_on_ok`
        #                events are returned but sometimes also `runner_on_start`.
        #                So far it has not been consistent (works in Standalone not on
        #                Cluster) while we get to the bottom of it we will filter on
        #                `runner_on_ok` for now.
        events_pg = command_pg.get_related('events', event__startswith='runner_on_ok')
        all_events = command_pg.get_related('events')
        assert events_pg.count == expected_count, \
            'Events did not match, expected {} runner_on_ok event but found {}'.format(expected_count, all_events)

    @pytest.mark.ansible_integration
    def test_launch_with_unmatched_limit_value(self, host, ssh_credential, api_ad_hoc_commands_pg, ansible_version_cmp):
        """Verify that launching an ad hoc command without matching host fails appropriately."""
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
        # Before 2.0.1.0, we expect job to be successful
        if ansible_version_cmp('2.0.1.0') < 0:
            job_pg.assert_successful()
        # Between 2.0.1.0 and 2.2.0.0 we expect job to fail
        elif ansible_version_cmp('2.2.0.0') < 0:
            assert job_pg.status == "failed", "Unexpected job_pg.status - %s." % job_pg
            assert "--limit does not match any hosts" in job_pg.result_stdout, \
                "Unexpected job_pg.result_stdout when launching an ad hoc command with an unmatched limit."
        # After 2.2.0.0 we expect job to be successful
        # See https://github.com/ansible/ansible/issues/17762
        else:
            job_pg.assert_successful()
            assert "[WARNING]: No hosts matched, nothing to do" in job_pg.result_stdout, \
                "Unexpected job_pg.result_stdout when launching an ad hoc command with an unmatched limit."

    def test_relaunch_command_with_privileged_users(
        self, host,
        ssh_credential,
        api_ad_hoc_commands_pg,
        api_unified_jobs_pg,
        privileged_users,
        user_password
    ):
        """Verifies that privileged users can relaunch commands."""
        use_role_pg = ssh_credential.get_object_role('use_role')
        for privileged_user in privileged_users:
            # give privileged user 'use_role' permissions
            with pytest.raises(exc.NoContent):
                use_role_pg.get_related('users').post(dict(id=privileged_user.id))

            # create payload
            payload = dict(inventory=host.inventory,
                           credential=ssh_credential.id,
                           module_name="ping", )

            with self.current_user(privileged_user.username, user_password):
                # post payload to ad_hoc_commands endpoint
                command = api_ad_hoc_commands_pg.post(payload).wait_until_completed()

                # verify that the first ad hoc command ran successfully
                command.assert_successful()

                # navigate to relaunch_pg and assert on relaunch_pg value
                relaunch_pg = command.get_related('relaunch')
                assert not relaunch_pg.passwords_needed_to_start

                # relaunch the job and assert success
                relaunched_command = command.relaunch().wait_until_completed()
                relaunched_command.assert_successful()

    def test_relaunch_command_with_unprivileged_users(self, ad_hoc_with_status_completed, unprivileged_users, user_password):
        """Verifies that unprivileged users cannot relaunch a command originally launched by admin."""
        relaunch_pg = ad_hoc_with_status_completed.get_related('relaunch')

        # relaunch the job and assert success
        for unprivileged_user in unprivileged_users:
            with self.current_user(unprivileged_user.username, user_password):
                with pytest.raises(exc.Forbidden):
                    relaunch_pg.post()

    def test_relaunch_command_with_ask_credential_and_passwords(
        self, request,
        ad_hoc_command_with_multi_ask_credential_and_password_in_payload,
        api_unified_jobs_pg
    ):
        """Tests that command relaunches work when supplied with the right passwords."""
        # create payload
        payload = dict(ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       become_password=self.credentials['ssh']['become_password'],
                       extra_vars={}, )

        # relaunch command and assert successful
        relaunched_command = ad_hoc_command_with_multi_ask_credential_and_password_in_payload.relaunch(payload).wait_until_completed()
        relaunched_command.assert_successful()

    def test_relaunch_command_with_ask_credential_and_without_passwords(
        self, request,
        ad_hoc_command_with_multi_ask_credential_and_password_in_payload,
        api_unified_jobs_pg
    ):
        """Tests that command relaunches fail when supplied without the right passwords."""
        relaunch_pg = ad_hoc_command_with_multi_ask_credential_and_password_in_payload.get_related('relaunch')

        # create payload
        payload = dict(extra_vars={}, )

        # post to relaunch_pg
        with pytest.raises(exc.BadRequest):
            relaunch_pg.post(payload)

    @pytest.mark.serial
    @pytest.mark.parametrize('extra_vars, exp_stdout', [("{'test': 'json'}", "json"), ("---\ntest: yaml", "yaml")])
    def test_launch_ahc_with_extra_vars(self, v2, factories, extra_vars, exp_stdout):
        # Need to set this so that templating is allowed
        api_settings_jobs_pg = v2.settings.get().get_endpoint('jobs')
        payload = dict(ALLOW_JINJA_IN_EXTRA_VARS='always')
        api_settings_jobs_pg.patch(**payload)

        host = factories.host()
        ahc = factories.ad_hoc_command(inventory=host.ds.inventory, module_name='shell', module_args='echo {{test}}',
                                          extra_vars=extra_vars).wait_until_completed()
        ahc.assert_successful()
        assert exp_stdout in ahc.result_stdout

    def test_launch_with_blacklisted_extra_vars(self, factories):
        with pytest.raises(exc.BadRequest) as e:
            factories.ad_hoc_command(extra_vars="{'ansible_connection': 'local', 'ansible_ssh': 127.0.0.1}")
        assert e.value[1]['extra_vars'] == ['ansible_ssh, ansible_connection are prohibited from use in ad hoc commands.']

    def test_relaunch_with_deleted_related(self, ad_hoc_with_status_completed, deleted_object):
        """Verify that relaunching a job with deleted related fails."""
        # verify that the first ad hoc command ran successfully
        ad_hoc_with_status_completed.assert_successful()

        # navigate to relaunch_pg and assert on relaunch_pg value
        relaunch_pg = ad_hoc_with_status_completed.get_related('relaunch')
        assert not relaunch_pg.passwords_needed_to_start

        # relaunch the command
        with pytest.raises(exc.BadRequest):
            relaunch_pg.post()

    @pytest.mark.ansible_integration
    @pytest.mark.fixture_args(module_name='shell', module_args='exit 1', job_type='check')
    def test_launch_with_check(self, host, ssh_credential, ad_hoc_with_status_completed):
        """Verifies check command behavior."""
        ad_hoc_with_status_completed.assert_successful()

        # check command attributes
        assert ad_hoc_with_status_completed.job_type == 'check'
        assert "--check" in ad_hoc_with_status_completed.job_args, \
            "Launched a check command but '--check' not present in job_args."

        # check that target task skipped
        matching_job_events = ad_hoc_with_status_completed.get_related('events', event='runner_on_skipped')
        assert matching_job_events.count == 1, \
            "Unexpected number of matching job events (%s != 1)" % matching_job_events.count

    @pytest.mark.serial
    def test_launch_ahc_with_diff(self, factories, api_settings_jobs_pg, update_setting_pg):
        host = factories.host()
        payload = dict(AD_HOC_COMMANDS=['file'])
        update_setting_pg(api_settings_jobs_pg, payload)
        ahc = factories.ad_hoc_command(inventory=host.ds.inventory, module_name='file', module_args='dest=/tmp/test_directory, state=touch',
                                          diff_mode=True).wait_until_completed()

        ahc.assert_successful()
        assert ahc.diff_mode
        assert '--- before' in ahc.result_stdout
        assert '+++ after' in ahc.result_stdout

    def test_ad_hoc_activity_stream(self, api_ad_hoc_commands_pg, ad_hoc_with_status_completed):
        """Verifies that launching an ad hoc command updates the activity stream."""
        # find command and navigate to command page
        ad_hoc_commands_pg = api_ad_hoc_commands_pg.get(id=ad_hoc_with_status_completed.id)
        assert ad_hoc_commands_pg.count == 1, \
            "command launched (id:%s) but unable to find matching " \
            "job." % ad_hoc_with_status_completed.id
        ad_hoc_command_pg = ad_hoc_commands_pg.results[0]

        # verify that activity stream populated after launch
        activity_stream_pg = ad_hoc_command_pg.get_related('activity_stream')
        assert activity_stream_pg.count == 1, "Activity stream not populated."

    @pytest.mark.yolo
    def test_command_page_update(self, org_admin, user_password, host, ssh_credential, api_ad_hoc_commands_pg):
        """Tests that deleting related objects will be reflected in the updated command page."""
        use_role_pg = ssh_credential.get_object_role('use_role')
        inventory_pg = host.get_related('inventory')

        # associate ssh_credential with org_admin
        with pytest.raises(exc.NoContent):
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
        ad_hoc_command_pg.assert_successful()

        # delete related objects
        inventory_pg.delete().wait_until_deleted()
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

    @pytest.mark.parametrize('extra_var, attr', [
        ['name', 'username'],
        ['id', 'id'],
        ['first_name', 'first_name'],
        ['last_name', 'last_name'],
        ['email', 'email'],
    ])
    @pytest.mark.parametrize('prefix', ['awx', 'tower'])
    def test_awx_metavars_for_adhoc_commands(self, v2, factories, host, update_setting_pg, extra_var, attr, prefix):
        admin_user = factories.user(first_name='Joe', last_name='Admin', is_superuser=True)
        value = str(getattr(admin_user, attr))
        var_name = '{}_user_{}'.format(prefix, extra_var)
        update_setting_pg(
            v2.settings.get().get_endpoint('jobs'),
            dict(ALLOW_JINJA_IN_EXTRA_VARS='always')
        )
        with self.current_user(admin_user):
            ahc = factories.ad_hoc_command(inventory=host.ds.inventory, module_name='shell',
                                              module_args='echo "%s={{ %s }}"' % (attr, var_name)).wait_until_completed()
        assert "=".join([attr, value]) in ahc.result_stdout

    def test_output_unicode(self, v2, factories):
        host = factories.host()

        ahc = factories.ad_hoc_command(inventory=host.ds.inventory, module_name='shell',
                                          module_args="python -c 'print(\"\xe8\xb5\xb7\xe5\x8b\x95\" * 1000000)'").wait_until_completed()
        ahc.assert_successful()
        assert "\xe8\xb5\xb7\xe5\x8b\x95" * 1000000 in ahc.result_stdout
