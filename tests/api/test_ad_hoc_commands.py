import pytest
import fauxfactory
import json
import common.exceptions
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
def ad_hoc_command_with_multi_ask_credential_and_password_in_payload(request, inventory, ssh_credential_multi_ask, api_ad_hoc_commands_pg, testsetup):
    '''
    Launch command with multi_ask credential and passwords in the payload.
    '''
    # create payload
    payload = dict(inventory=inventory.id,
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
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_get_as_superuser(self, inventory):
        '''
        Verify that a superuser account is able to GET from the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = inventory.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    def test_post_as_superuser(self, inventory, ssh_credential):
        '''
        Verify that a superuser account is able to POST to the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = inventory.get_related('ad_hoc_commands')

        # create payload
        payload = dict(inventory=inventory.id,
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
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_get_as_superuser(self, group):
        '''
        Verify that a superuser account is able to GET from the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = group.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    def test_post_as_superuser(self, group, inventory, ssh_credential):
        '''
        Verify that a superuser account is able to POST to the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = group.get_related('ad_hoc_commands')

        # create payload
        payload = dict(inventory=inventory.id,
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
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_get_as_superuser(self, host):
        '''
        Verify that a superuser account is able to GET from the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = host.get_related('ad_hoc_commands')
        ad_hoc_commands_pg.get()

    def test_post_as_superuser(self, host, inventory, ssh_credential):
        '''
        Verify that a superuser account is able to POST to the ad_hoc_commands endpoint.
        '''
        ad_hoc_commands_pg = host.get_related('ad_hoc_commands')

        # create payload
        payload = dict(inventory=inventory.id,
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
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_get(self, api_ad_hoc_commands_pg, all_users, user_password):
        '''
        Verify that privileged users are able to GET from the ad_hoc_commands endpoint.
        '''
        for user in all_users:
            with self.current_user(user.username, user_password):
                api_ad_hoc_commands_pg.get()

    def test_post_as_privileged_user(self, inventory, ssh_credential, api_ad_hoc_commands_pg, privileged_users, user_password):
        '''
        Verify that a superuser account is able to post to the ad_hoc_commands endpoint.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as privileged user
        for privileged_user in privileged_users:
            ssh_credential.patch(user=privileged_user.id)
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
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    api_ad_hoc_commands_pg.post(payload)

    def test_launch_without_module_name(self, inventory, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Verifies that if you post without specifiying module_name that the command module is run.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
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

    @pytest.mark.trello('https://trello.com/c/4jG0xMqo')
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
            with pytest.raises(common.exceptions.BadRequest_Exception):
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
        exc_info = pytest.raises(common.exceptions.BadRequest_Exception, api_ad_hoc_commands_pg.post, payload)
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
            "Unexpected command status after cancelling command (status:%s)" % \
            ad_hoc_with_status_pending.status

    def test_launch_with_ask_credential_and_passwords_in_payload(self, inventory, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
        '''
        Verifies that launching a command with an ask credential succeeds when supplied with proper passwords.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
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
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, inventory, ssh_credential_multi_ask, api_ad_hoc_commands_pg):
        '''
        Verifies that launching a command with an ask credential fails when not supplied with required passwords.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential_multi_ask.id,
                       module_name="ping", )

        # post the command
        with pytest.raises(common.exceptions.BadRequest_Exception):
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

    @pytest.mark.parametrize("limit_value,expected_count", [
        ("", 16),
        ("all", 16),
        ("host-14", 1),
        ("group-1", 6),
        ("group*:&group-1:!duplicate_host", 5),
        ("duplicate_host", 1)
    ])
    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import json

inv = dict(_meta=dict(hostvars={}), hosts=[])

# create three groups and put duplicate_host in all three groups
for i in range(3):
    inv['group-'+str(i)] = list()
    host = "duplicate_host"
    inv['group-'+str(i)].append(host)
    inv['_meta']['hostvars'][host] = dict(ansible_ssh_host='127.0.0.1', ansible_connection='local')

# create fifteen hosts, five per each group
for i in range(15):
    host = 'host-'+str(i)
    inv['group-'+str(i%3)].append(host)
    inv['_meta']['hostvars'][host] = dict(ansible_ssh_host='127.0.0.1', ansible_connection='local')

print json.dumps(inv, indent=2)
''')
    def test_launch_with_various_limit_values(
            self, limit_value,
            expected_count,
            custom_inventory_source,
            custom_inventory_update_with_status_completed,
            ssh_credential,
            api_ad_hoc_commands_pg
    ):
        '''
        Verifies payloads with different values for "limit" behave as expected.
        '''
        custom_inventory_update_with_status_completed

        # create payload
        payload = dict(inventory=custom_inventory_source.inventory,
                       credential=ssh_credential.id,
                       module_name="ping",
                       limit=limit_value)

        # post the command
        command_pg = api_ad_hoc_commands_pg.post(payload).wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

        # assert that command run on correct number of hosts
        events_pg = command_pg.get_related('events')
        assert events_pg.count == expected_count

    def test_relaunch_command_with_privileged_users(
        self, inventory,
        ssh_credential,
        api_ad_hoc_commands_pg,
        api_unified_jobs_pg,
        privileged_users,
        user_password
    ):
        '''
        Verifies that privileged users can relaunch commands.
        '''
        for privileged_user in privileged_users:
            # patch the credential for the current user
            ssh_credential.patch(user=privileged_user.id)

            # create payload
            payload = dict(inventory=inventory.id,
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
                with pytest.raises(common.exceptions.Forbidden_Exception):
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
        with pytest.raises(common.exceptions.BadRequest_Exception):
            relaunch_pg.post(payload)

    @pytest.mark.trello('https://trello.com/c/IbvBelXJ')
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
        with pytest.raises(common.exceptions.BadRequest_Exception):
            relaunch_pg.post()

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

    def test_command_page_update(self, org_admin, user_password, inventory, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Tests that deleting related objects will be reflected in the updated command page.
        '''
        # modify credential for org_admin
        ssh_credential.patch(user=org_admin.id)

        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload to ad_hoc_commands endpoint
        with self.current_user(org_admin.username, user_password):
            ad_hoc_command_pg = api_ad_hoc_commands_pg.post(payload)

        # verify that the first ad hoc command ran successfully
        ad_hoc_command_pg.wait_until_completed()
        assert ad_hoc_command_pg.is_successful, "Ad hoc command unsuccessful - %s" % ad_hoc_command_pg

        # delete related objects
        inventory.delete()
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
    def test_included_modules(self, inventory, ssh_credential, api_ad_hoc_commands_pg, AD_HOC_COMMANDS, ad_hoc_module_name_choices):
        '''
        Verifies that adding additional modules to ad_hoc.py unlocks additional modules.
        '''
        # assess options choices
        assert 'shell' in ad_hoc_module_name_choices

        # create payload
        payload = dict(inventory=inventory.id,
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
    def test_excluded_modules(self, inventory, ssh_credential, api_ad_hoc_commands_pg, AD_HOC_COMMANDS, ad_hoc_module_name_choices):
        '''
        Verifies that removed modules are no longer callable.
        '''
        # assess options choices
        assert not ad_hoc_module_name_choices

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
            exc_info = pytest.raises(common.exceptions.BadRequest_Exception, api_ad_hoc_commands_pg.post, payload)
            result = exc_info.value[1]

            # assess result
            assert result == {'module_name': ['Select a valid choice. %s is not one of the available choices.' % module_name]}, \
                "Unexpected response upon launching ad hoc command %s not included in " \
                "ad_hoc.py. %s" % (module_name, json.dumps(result))

    @pytest.mark.fixture_args(ad_hoc_commands=[])
    def test_relaunch_with_excluded_module(self, ad_hoc_with_status_completed, inventory, ssh_credential, api_ad_hoc_commands_pg, AD_HOC_COMMANDS):
        '''
        Verifies that you cannot relaunch a command which has been removed
        from ad_hoc_commands.py.
        '''
        relaunch_pg = ad_hoc_with_status_completed.get_related('relaunch')

        # relaunch ad hoc command
        exc_info = pytest.raises(common.exceptions.BadRequest_Exception, relaunch_pg.post)
        result = exc_info.value[1]

        # assess result
        assert result == {"module_name": ["Select a valid choice. ping is not one of the available choices."]}, \
            "Unexpected response when relaunching ad hoc command whose module " \
            "has been removed from ad_hoc.py. %s" % json.dumps(result)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Ad_Hoc_Permissions(Base_Api_Test):
    '''
    Tests ad hoc permissions.
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_unprivileged_user_with_no_permissions(self, inventory, ssh_credential, api_ad_hoc_commands_pg, unprivileged_users, user_password):
        '''
        Verify that unprivileged users without ad hoc launch cannot launch ad hoc commands.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as unprivileged user
        for unprivileged_user in unprivileged_users:
            # grant the user permissions
            unprivileged_user.add_permission('read', inventory=inventory.id)
            # associate the credential with the user
            ssh_credential.patch(user=unprivileged_user.id)
            # post the command as the privileged user
            with self.current_user(unprivileged_user.username, user_password):
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    api_ad_hoc_commands_pg.post(payload)

    def test_unprivileged_user_with_readexecute_permissions(self, inventory, ssh_credential, api_ad_hoc_commands_pg, unprivileged_users, user_password):
        '''
        Verify that unprivileged users with ad hoc launch can post to the ad_hoc_commands endpoint.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as unprivileged user
        for unprivileged_user in unprivileged_users:
            # grant the user permissions
            unprivileged_user.add_permission('read', inventory=inventory.id, run_ad_hoc_commands=True)
            # associate the credential with the user
            ssh_credential.patch(user=unprivileged_user.id)
            # post the command as the privileged user
            with self.current_user(unprivileged_user.username, user_password):
                command_pg = api_ad_hoc_commands_pg.post(payload)

            # assert command successful
            command_pg.wait_until_completed()
            assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

    def test_privileged_user_with_no_permissions(self, inventory, ssh_credential, api_ad_hoc_commands_pg, privileged_users, user_password):
        '''
        Verify that privileged users can post to the ad_hoc_commands endpoint without permissions.
        '''
        # create payload
        payload = dict(inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as unprivileged user
        for privileged_user in privileged_users:
            # associate the credential with the user
            ssh_credential.patch(user=privileged_user.id)
            # post the command as the privileged user
            with self.current_user(privileged_user.username, user_password):
                command_pg = api_ad_hoc_commands_pg.post(payload)

            # assert command successful
            command_pg.wait_until_completed()
            assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg
