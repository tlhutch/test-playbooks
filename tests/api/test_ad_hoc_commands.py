import pytest
import fauxfactory
import common.exceptions
from tests.api import Base_Api_Test

'''
Tests that span all four endpoints
-[X] Four tests - that super user can GET from all four ad hoc endpoints. Tests will be housed in respective modules.
-[X] Test that POST works for superuser on all four endpoints

Tests for the main api/v1/ad_hoc_commands endpoint
-[X] Verify that privileged users can launch a command from api/v1/ad_hoc_commands
-[X] Verify that unprivileged users cannot launch commands
-[] Verify that an org user with the correct permissions can launch a command

-[X] Test that posts without specifying module defaults to command
-[X] Verify that cancelling a command works
-[X] Launching with ask-credential (valid passwords, without passwords, with invalid passwords)
-[] Launching with no limit
-[] With limit=all
-[] with limit=$hosts
-[] with limit=$groups
-[] with limit=no match
-[] Launching with args => that the args are passed correctly (TODO: discussion church passing args as string/JSON file???)

-[X] Verify that privileged users can relaunch a command
-[X] Verify that unprivileged users cannot relaunch a command
-[X] Verify that command relaunches with deleted related fail
-[X] Verify relaunches with ask credential with both negative and positive cases

Stranger situations
-[X] Simple test: launch a command and assert that the activity stream gets populated
-[] changing settings.py and validating that you can new launch with new module names
-[] Launching a command with an invalid payload <= loop through required in options
-[X] Verify that deleting related is reflected correctly in the command page
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
    payload = dict(job_type="run",
                   inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post payload as unprivileged user
        for unprivileged_user in unprivileged_users:
            with self.current_user(unprivileged_user.username, user_password):
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    api_ad_hoc_commands_pg.post(payload)

    def test_launch_without_module_name(self, inventory, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Verifies that if you post without specifiying module_name that the command module is run.
        '''
        # create payload
        payload = dict(job_type="run",
                       inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
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

    @pytest.mark.skipif(True, reason="not yet implemented")
    def test_post_with_no_limit(self, preloaded_inventory, ssh_credential, api_ad_hoc_commands_pg, api_hosts_pg):
        '''
        Verifies that posting with nothing for limit results in a command being run on all hosts.
        '''
        commands_pg = api_ad_hoc_commands_pg.get()

        # create payload
        payload = dict(job_type="run",
                       inventory=preloaded_inventory.id,
                       credential=ssh_credential.id,
                       module_name="ping", )

        # post the command
        command_pg = commands_pg.post(payload)

        # assert success
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

        # assert that command run on all hosts in inventory
        hosts_pg = api_hosts_pg.get()
        for host in hosts_pg.results:
            ad_hoc_command_events_pg = host.get_related('ad_hoc_commands')
            assert ad_hoc_command_events_pg.count == 1
            assert ad_hoc_command_events_pg.results[0].id == command_pg.id

    @pytest.mark.skipif(True, reason="not yet implemented")
    def test_post_with_limit_all(self, preloaded_inventory, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Verifies that posting with limit = "all" runs a commands on all hosts.
        '''
        commands_pg = api_ad_hoc_commands_pg.get()

        # create payload
        payload = dict(job_type="run",
                       credential=ssh_credential.id,
                       module_name="ping",
                       limit="all", )

        # post the command
        command_pg = commands_pg.post(payload)

        # assert success
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

        # assert that command run on all hosts in inventory

    @pytest.mark.skipif(True, reason="not yet implemented")
    def test_post_with_limit_hosts(self, preloaded_inventory, ssh_credential, api_ad_hoc_commands_pg):
        '''
        Verifies that specific host selection works.
        '''
        commands_pg = api_ad_hoc_commands_pg.get()

        # create payload
        payload = dict(job_type="run",
                       credential=ssh_credential.id,
                       module_name="ping",
                       limit="", )

        # post the command
        command_pg = commands_pg.post(payload)

        # assert success
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

        # assert that command run on specific hosts

    @pytest.mark.skipif(True, reason="not yet implemented")
    def test_post_with_limit_groups(self, inventory, ssh_credential, api_ad_hoc_commands_pg, privileged_users, user_password):
        '''
        Verifies that specific group selection works.
        '''
        commands_pg = api_ad_hoc_commands_pg.get()

        # create payload
        payload = dict(job_type="run",
                       credential=ssh_credential.id,
                       module_name="ping",
                       limit="all", )

        # post the command
        command_pg = commands_pg.post(payload)

        # assert success
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

        # assert that hosts run on specific groups

    @pytest.mark.skipif(True, reason="not yet implemented")
    def test_post_with_no_match_limit(self, inventory, ssh_credential, api_ad_hoc_commands_pg, privileged_users, user_password):
        '''
        Verifies that if no hosts are matched that no commands are run.
        '''
        commands_pg = api_ad_hoc_commands_pg.get()

        # create payload
        payload = dict(job_type="run",
                       credential=ssh_credential.id,
                       module_name="ping",
                       limit="non-existent host", )

        # post the command
        command_pg = commands_pg.post(payload)

        # assert success
        command_pg.wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s " % command_pg

        # assert that command run on no hosts

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
            payload = dict(job_type="run",
                           inventory=inventory.id,
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
        payload = dict(job_type="run",
                       inventory=inventory.id,
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
