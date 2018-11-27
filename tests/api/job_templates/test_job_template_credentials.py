from distutils.version import LooseVersion
import logging
import six

from towerkit.config import config
import towerkit.exceptions as exc
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateCredentials(APITest):

    def test_job_template_creation_without_credential(self, request, v2, factories):
        payload = factories.v2_job_template.payload()
        del payload['credential']
        jt = v2.job_templates.post(payload)
        request.addfinalizer(jt.silent_delete)

    @pytest.mark.github('https://github.com/ansible/tower/issues/3077')
    def test_job_template_cannot_have_multiple_same_type(self, factories):
        ct = factories.credential_type()
        cred1 = factories.v2_credential(credential_type=ct)
        cred2 = factories.v2_credential(credential_type=ct)
        assert cred1.credential_type == cred2.credential_type

        jt = factories.v2_job_template(credential=None)
        jt.add_credential(cred1)
        with pytest.raises(exc.BadRequest) as e:
            jt.add_credential(cred2)
        assert e.value.message['error'] == six.text_type(
            'Cannot assign multiple {} credentials.'
        ).format(ct.name)


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateLaunchCredentials(APITest):

    def test_launch_without_credential(self, job_template_no_credential):
        """Verify the job launch endpoint allows launching a job template without a credential."""
        launch = job_template_no_credential.related.launch.get()

        assert launch.can_start_without_user_input
        assert not launch.ask_credential_on_launch
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        # launch the job_template without providing a credential
        job = job_template_no_credential.launch().wait_until_completed()
        assert job.is_successful
        assert job.credential is None

        job_template_no_credential.ask_credential_on_launch = True
        job = job_template_no_credential.launch().wait_until_completed()
        assert job.is_successful
        assert job.credential is None

    def test_launch_with_linked_credential(self, job_template_prompt_for_credential, ssh_credential):
        """Verify the job template launch endpoint requires user input when using a linked credential and
        `ask_credential_on_launch`.
        """
        job_template_prompt_for_credential.credential = ssh_credential.id
        launch = job_template_prompt_for_credential.related.launch.get()

        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        job = job_template_prompt_for_credential.launch().wait_until_completed()

        assert job.is_successful
        assert job.credential == ssh_credential.id

    def test_launch_with_payload_credential(self, job_template_prompt_for_credential, ssh_credential):
        """Verify the job launch endpoint allows launching a job template when providing a credential."""
        launch = job_template_prompt_for_credential.related.launch.get()

        assert not launch.can_start_without_user_input
        assert launch.ask_credential_on_launch
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        job = job_template_prompt_for_credential.launch(dict(credential=ssh_credential.id)).wait_until_completed()

        assert job.is_successful
        assert job.credential == ssh_credential.id

    def test_launch_with_invalid_credential_in_payload(self, job_template_prompt_for_credential):
        """Verify the job launch endpoint throws 400 error when launching with invalid credential id"""
        invalid_and_error = [('one', "Incorrect type. Expected pk value, received unicode."),
                             (0, 'Invalid pk "0" - object does not exist.'),
                             (False, 'Invalid pk "False" - object does not exist.'),
                             ({}, 'Incorrect type. Expected pk value, received OrderedDict.')]
        for invalid, error in invalid_and_error:
            with pytest.raises(exc.BadRequest) as e:
                job_template_prompt_for_credential.launch(dict(credential=invalid))
            assert e.value.message['credentials'] == [error]

    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, job_template_prompt_for_credential,
                                                                         ssh_credential_ask):
        """Verify that attempts to launch a JT when providing an 'ASK' credential at launch time without
        providing the required passwords raise 400 error.
        """
        launch = job_template_prompt_for_credential.related.launch.get()

        # launch the JT providing the credential in the payload, but no passwords_needed_to_start
        with pytest.raises(exc.BadRequest) as exc_info:
            launch.post(dict(credential=ssh_credential_ask.id))
        result = exc_info.value[1]

        assert 'passwords_needed_to_start' in result
        assert result['passwords_needed_to_start'] == ssh_credential_ask.expected_passwords_needed_to_start

    def test_launch_with_ask_credential_and_passwords_in_payload(self, job_template_prompt_for_credential, ssh_credential_ask):
        """Verify launching a JT when providing an 'ASK' credential at launch time with required passwords
        is functional
        """
        job = job_template_prompt_for_credential.launch(dict(credential=ssh_credential_ask.id,
                                                        ssh_password=config.credentials.ssh.password,
                                                        ssh_key_unlock=config.credentials.ssh.encrypted.ssh_key_unlock,
                                                        become_password=config.credentials.ssh.become_password))
        assert job.wait_until_completed().is_successful
        assert job.credential == ssh_credential_ask.id

    def test_launch_split_JT_with_ask_credential_and_passwords_in_payload(self, job_template_prompt_for_credential,
                                                                          factories, ssh_credential_ask):
        """Verify functionality of providing credential & passwords with a split JT
        """
        factories.host(inventory=job_template_prompt_for_credential.ds.inventory)
        assert job_template_prompt_for_credential.ds.inventory.get_related('hosts').count == 2
        job_template_prompt_for_credential.job_slice_count = 2
        wfj = job_template_prompt_for_credential.launch(dict(credential=ssh_credential_ask.id,
                                                        ssh_password=config.credentials.ssh.password,
                                                        ssh_key_unlock=config.credentials.ssh.encrypted.ssh_key_unlock,
                                                        become_password=config.credentials.ssh.become_password))
        assert wfj.wait_until_completed().is_successful
        job = wfj.get_related('workflow_nodes').results.pop().get_related('job')
        assert job.credential == ssh_credential_ask.id
        assert job.is_successful

    @pytest.mark.ansible_integration
    @pytest.mark.skip_openshift
    def test_launch_with_unencrypted_ssh_credential(self, ansible_runner, job_template,
                                                    unencrypted_ssh_credential_with_ssh_key_data):
        (credential_type, credential) = unencrypted_ssh_credential_with_ssh_key_data

        job_template.credential = credential.id

        launch = job_template.related.launch.get()
        assert not launch.passwords_needed_to_start

        job = job_template.launch().wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "unencrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job.is_successful
            else:
                assert job.status == 'error'
                runtime_error = "RuntimeError: It looks like you're trying to use a private key in OpenSSH format"
                assert runtime_error in job.result_traceback
        else:
            assert job.is_successful

    @pytest.mark.ansible_integration
    @pytest.mark.skip_openshift
    def test_launch_with_encrypted_ssh_credential(self, ansible_runner, job_template,
                                                  encrypted_ssh_credential_with_ssh_key_data):
        (credential_type, credential) = encrypted_ssh_credential_with_ssh_key_data

        job_template.credential = credential.id

        launch = job_template.get_related('launch')
        assert launch.passwords_needed_to_start == [u'ssh_key_unlock']

        job = job_template.launch(dict(ssh_key_unlock='fo0m4nchU'))
        job.wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "encrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job.is_successful
            else:
                assert job.status == 'error'
                runtime_error = "RuntimeError: It looks like you're trying to use a private key in OpenSSH format"
                assert runtime_error in job.result_traceback
        else:
            assert job.is_successful

    def test_launch_with_team_credential(self, factories, job_template_prompt_for_credential, team, team_ssh_credential):
        """Verifies that a team user can use a team credential to launch a job template."""
        team_user = factories.user()
        team.add_user(team_user)
        job_template_prompt_for_credential.set_object_roles(team_user, 'execute')

        with self.current_user(team_user.username, team_user.password):
            job = job_template_prompt_for_credential.launch(dict(credential=team_ssh_credential.id)).wait_until_completed()
            assert job.is_successful
            assert job.credential == team_ssh_credential.id

    def test_launch_with_multiple_credentials(self, v2, factories, custom_cloud_credentials, custom_network_credentials):
        machine_cred = factories.v2_credential()
        vault_cred1 = factories.v2_credential(kind='vault', vault_password='tower', vault_id='vault1')
        vault_cred2 = factories.v2_credential(kind='vault', vault_password='tower', vault_id='vault2')

        creds = [machine_cred, vault_cred1, vault_cred2]
        creds.extend([c for c in custom_cloud_credentials])
        creds.extend([c for c in custom_network_credentials])
        jt = factories.v2_job_template(credential=None, ask_credential_on_launch=True)
        jt.ds.inventory.add_host()
        job = jt.launch(dict(credentials=[c.id for c in creds]))
        assert job.wait_until_completed().is_successful

        job_creds = job.related.credentials.get().results
        assert set(c.id for c in job_creds) == set(c.id for c in creds)
        assert len(job_creds) == len(creds)

    def test_launch_with_multiple_credentials_but_ask_credential_on_launch_false(self, v2, factories,
                                                                                 custom_cloud_credentials,
                                                                                 custom_network_credentials):
        machine_cred = factories.v2_credential()
        vault_cred1 = factories.v2_credential(kind='vault', vault_password='tower', vault_id='vault1')
        vault_cred2 = factories.v2_credential(kind='vault', vault_password='tower', vault_id='vault2')

        creds = [machine_cred, vault_cred1, vault_cred2]
        creds.extend([c for c in custom_cloud_credentials])
        creds.extend([c for c in custom_network_credentials])
        jt = factories.v2_job_template(credential=None)
        jt.ds.inventory.add_host()
        job = jt.launch(dict(credentials=[c.id for c in creds]))
        assert job.wait_until_completed().is_successful
        assert job.related.credentials.get().count == 0

    def test_provide_additional_vault_credential_on_launch(self, v2, factories):
        jt = factories.v2_job_template(credential=None, ask_credential_on_launch=True)
        jt.ds.inventory.add_host()

        vault_cred1 = factories.v2_credential(kind='vault', vault_password='tower', vault_id='vault1')
        vault_cred2 = factories.v2_credential(kind='vault', vault_password='tower', vault_id='vault2')
        jt.add_credential(vault_cred1)

        with pytest.raises(exc.BadRequest) as e:
            jt.launch(dict(credentials=[vault_cred2.id]))
        error_msg = (u'Removing Vault (id={0.inputs.vault_id}) credential at launch time without replacement '
                     'is not supported. Provided list lacked credential(s): {0.name}-{0.id}.').format(vault_cred1)
        assert e.value.message == {'credentials': [error_msg]}

        job = jt.launch(dict(credentials=[vault_cred1.id, vault_cred2.id]))
        assert job.wait_until_completed().is_successful

        job_creds = job.related.credentials.get().results
        assert set(c.id for c in job_creds) == set([vault_cred1.id, vault_cred2.id])
        assert job.related.credentials.get().count == 2

    def test_cannot_mix_old_and_new_launch_params_for_credentials(self, v2, factories, custom_cloud_credentials, custom_network_credentials):
        jt = factories.v2_job_template(credential=None, ask_credential_on_launch=True)
        jt.ds.inventory.add_host()

        machine_cred = factories.v2_credential()
        vault_cred1 = factories.v2_credential(kind='vault', vault_password='secret1', vault_id='vault1')
        vault_cred2 = factories.v2_credential(kind='vault', vault_password='secret2', vault_id='vault2')
        bad_payloads = [dict(credential=machine_cred.id, credentials=[vault_cred1.id]),
                        dict(vault_credential=vault_cred1.id, credentials=[vault_cred2.id]),
                        dict(extra_credentials=[c.id for c in custom_cloud_credentials], credentials=[machine_cred.id]),
                        dict(extra_credentials=[c.id for c in custom_network_credentials], credentials=[machine_cred.id])]
        for payload in bad_payloads:
            with pytest.raises(exc.BadRequest) as e:
                jt.launch(payload)
            assert e.value.message == {'error': "'credentials' cannot be used in combination with 'credential', 'vault_credential', or 'extra_credentials'."}


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateVaultCredentials(APITest):

    def test_job_template_creation_with_lone_vault_credential(self, request, v2, factories):
        payload = factories.v2_job_template.payload()
        del payload['credential']

        vault_credential = factories.v2_credential(kind='vault', vault_password='tower')
        payload['vault_credential'] = vault_credential.id

        jt = v2.job_templates.post(payload)
        request.addfinalizer(jt.delete)

        assert not jt.credential
        assert jt.vault_credential == vault_credential.id

    @pytest.mark.parametrize('v, cred_args', [['v1', dict(vault_password='tower', username='', password='',
                                                          ssh_key_data='', become_password='')],
                                              ['v2', dict(kind='vault', vault_password='tower')]])
    def test_decrypt_vaulted_playbook_with_vault_credential(self, factories, v, cred_args):
        host_factory = getattr(factories, 'host' if v == 'v1' else 'v2_host')
        cred_factory = getattr(factories, 'credential' if v == 'v1' else 'v2_credential')
        jt_factory = getattr(factories, 'job_template' if v == 'v1' else 'v2_job_template')

        host = host_factory()
        jt = jt_factory(inventory=host.ds.inventory, playbook='vaulted_debug_hostvars.yml')

        vault_cred = cred_factory(**cred_args)
        jt.vault_credential = vault_cred.id

        job = jt.launch().wait_until_completed()
        assert job.is_successful

        debug_tasks = job.related.job_events.get(host_name=host.name, task='debug', event__startswith='runner_on_ok').results
        assert len(debug_tasks) == 1
        assert debug_tasks[0].event_data.res.hostvars.keys() == [host.name]

    @pytest.mark.parametrize('v, cred_args', [['v1', dict(vault_password='ASK', username='', password='',
                                                          ssh_key_data='', become_password='')],
                                              ['v2', dict(kind='vault', vault_password='ASK')]])
    def test_decrypt_vaulted_playbook_with_lone_ask_on_launch_vault_credential(self, factories, v, cred_args):
        host_factory = getattr(factories, 'host' if v == 'v1' else 'v2_host')
        cred_factory = getattr(factories, 'credential' if v == 'v1' else 'v2_credential')
        jt_factory = getattr(factories, 'job_template' if v == 'v1' else 'v2_job_template')

        host = host_factory()
        vault_cred = cred_factory(**cred_args)
        jt = jt_factory(inventory=host.ds.inventory, playbook='vaulted_debug_hostvars.yml')
        jt.vault_credential = vault_cred.id
        jt.credential = None

        with pytest.raises(exc.BadRequest) as e:
            jt.launch().wait_until_completed()
        assert e.value.message == {'passwords_needed_to_start': ['vault_password']}

        job = jt.launch(dict(vault_password='tower')).wait_until_completed()
        assert job.is_successful

        debug_tasks = job.related.job_events.get(host_name=host.name, task='debug', event__startswith='runner_on_ok').results
        assert len(debug_tasks) == 1
        assert debug_tasks[0].event_data.res.hostvars.keys() == [host.name]

    def test_decrypt_vaulted_playbook_with_multiple_vault_credentials(self, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='multivault.yml')

        vault_cred1 = factories.v2_credential(kind='vault', vault_password='secret1', vault_id='first')
        vault_cred2 = factories.v2_credential(kind='vault', vault_password='secret2', vault_id='second')
        jt.add_credential(vault_cred1)
        jt.add_credential(vault_cred2)

        job = jt.launch().wait_until_completed()
        assert job.is_successful

        debug_tasks = job.related.job_events.get(host_name=host.name, task='debug', event__startswith='runner_on_ok').results
        assert len(debug_tasks) == 2
        assert any('First!' in task.stdout for task in debug_tasks)
        assert any('Second!' in task.stdout for task in debug_tasks)

    def test_decrypt_vaulted_playbook_with_multiple_ask_on_launch_vault_credentials(self, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='multivault.yml')

        vault_cred1 = factories.v2_credential(kind='vault', vault_password='ASK', vault_id='first')
        vault_cred2 = factories.v2_credential(kind='vault', vault_password='ASK', vault_id='second')
        jt.add_credential(vault_cred1)
        jt.add_credential(vault_cred2)

        with pytest.raises(exc.BadRequest) as e:
            jt.launch().wait_until_completed()
        assert set(e.value.message['passwords_needed_to_start']) == set(['vault_password.first', 'vault_password.second'])
        assert len(e.value.message['passwords_needed_to_start']) == 2

        payload = {'vault_password.first': 'secret1',
                   'vault_password.second': 'secret2'}

        job = jt.launch(payload).wait_until_completed()
        assert job.is_successful

        debug_tasks = job.related.job_events.get(host_name=host.name, task='debug', event__startswith='runner_on_ok').results
        assert len(debug_tasks) == 2
        assert any('First!' in task.stdout for task in debug_tasks)
        assert any('Second!' in task.stdout for task in debug_tasks)

    def test_cannot_assign_multiple_vault_credentials_with_same_vault_id(self, factories):
        jt = factories.v2_job_template()
        vault_cred1 = factories.v2_credential(kind='vault', vault_password='secret1', vault_id='foo')
        vault_cred2 = factories.v2_credential(kind='vault', vault_password='secret2', vault_id='foo')
        jt.add_credential(vault_cred1)
        with pytest.raises(exc.BadRequest) as e:
            jt.add_credential(vault_cred2)
        assert e.value.message == {'error': 'Cannot assign multiple Vault (id=foo) credentials.'}


@pytest.fixture(scope='class')
def custom_cloud_credentials(class_factories):
    cred_types = [class_factories.credential_type(kind='cloud') for _ in range(3)]
    return [class_factories.v2_credential(credential_type=cred_type) for cred_type in cred_types]


@pytest.fixture(scope='class')
def custom_network_credentials(class_factories):
    cred_types = [class_factories.credential_type(kind='net') for _ in range(3)]
    return [class_factories.v2_credential(credential_type=cred_type) for cred_type in cred_types]


@pytest.fixture(scope='class', params=('custom_cloud_credentials', 'custom_network_credentials'))
def custom_extra_credentials(request):
    return request.getfixturevalue(request.param)


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateExtraCredentials(APITest):

    def test_job_template_with_added_and_removed_custom_extra_credentials(self, factories, custom_extra_credentials):
        ssh_cred = factories.v2_credential()
        jt = factories.v2_job_template(credential=ssh_cred)

        assert jt.related.extra_credentials.get().count == 0

        extra_credentials = set()
        for cred in custom_extra_credentials:
            jt.add_extra_credential(cred)
            jt_extra_credentials = set([c.id for c in jt.related.extra_credentials.get().results])
            assert extra_credentials < jt_extra_credentials
            assert cred.id in jt_extra_credentials
            extra_credentials.add(cred.id)

        assert ssh_cred.id not in jt_extra_credentials

        for cred in custom_extra_credentials:
            jt.remove_extra_credential(cred)
            jt_extra_credentials = set([c.id for c in jt.related.extra_credentials.get().results])
            assert cred.id not in jt_extra_credentials
            extra_credentials.remove(cred.id)
            assert extra_credentials == jt_extra_credentials

        assert not jt_extra_credentials

    def test_confirm_scm_ssh_and_vault_credentials_disallowed(self, factories):
        jt = factories.v2_job_template()
        scm_cred = factories.v2_credential(kind='scm')
        ssh_cred = factories.v2_credential()
        vault_cred = factories.v2_credential(kind='vault', inputs=dict(vault_password='fake'))

        for cred in (scm_cred, ssh_cred, vault_cred):
            with pytest.raises(exc.BadRequest) as e:
                jt.add_extra_credential(cred)
            assert e.value.message == {'error': 'Extra credentials must be network or cloud.'}
            assert not jt.related.extra_credentials.get().results

    @pytest.fixture(scope='class')
    def v2_job_template(self, class_factories):
        return class_factories.v2_job_template()

    @pytest.mark.parametrize('credential_kind, kind_name',
                             [('aws', 'Amazon Web Services'),
                              ('gce', 'Google Compute Engine'),
                              ('azure_rm', 'Microsoft Azure Resource Manager'),
                              ('net', 'Network'),
                              ('openstack_v3', 'OpenStack'),
                              ('cloudforms', 'Red Hat CloudForms'),
                              ('satellite6', 'Red Hat Satellite 6'),
                              ('vmware', 'VMware vCenter')])
    def test_confirm_only_single_managed_by_tower_extra_credential_allowed(self, factories, v2_job_template,
                                                                           credential_kind, kind_name):
        cred_one, cred_two = [factories.v2_credential(kind=credential_kind) for _ in range(2)]

        v2_job_template.add_extra_credential(cred_one)

        with pytest.raises(exc.BadRequest) as e:
            v2_job_template.add_extra_credential(cred_two)
        assert e.value.message == {'error': 'Cannot assign multiple {} credentials.'.format(kind_name)}

        assert cred_two.id not in [c.id for c in v2_job_template.related.extra_credentials.get().results]

        v2_job_template.remove_extra_credential(cred_one)
        assert cred_one.id not in [c.id for c in v2_job_template.related.extra_credentials.get().results]

        v2_job_template.add_extra_credential(cred_two)
        assert cred_two.id in [c.id for c in v2_job_template.related.extra_credentials.get().results]

    def test_confirm_extra_credentials_injectors_are_sourced(self, request, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='ansible_env.yml')

        cloud_credentials = [factories.v2_credential(kind=cred_type) for cred_type in ('aws', 'gce')]
        cloud_credentials.append(factories.v2_credential(kind='azure_rm', cloud_environment='SomeEnvironment'))
        for cred in cloud_credentials:
            jt.add_extra_credential(cred)

        job = jt.launch().wait_until_completed()
        request.addfinalizer(job.delete)  # Noisy neighbor

        assert job.is_successful

        env_vars = ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AZURE_CLIENT_ID', 'AZURE_CLOUD_ENVIRONMENT', 'AZURE_SECRET',
                    'AZURE_SUBSCRIPTION_ID', 'AZURE_TENANT', 'GCE_EMAIL', 'GCE_CREDENTIALS_FILE_PATH', 'GCE_PROJECT')

        for env_var in env_vars:
            assert env_var in job.job_env

        ansible_env = job.related.job_events.get(host=host.id, task='debug').results.pop().event_data.res.ansible_env

        for env_var in env_vars:
            assert env_var in ansible_env

    def test_confirm_ask_on_launch_extra_credential_values_are_sourced(self, factories):
        input_one = dict(fields=[dict(id='field_one', label='FieldOne')])
        input_two = dict(fields=[dict(id='field_two', label='FieldTwo')])
        input_three = dict(fields=[dict(id='field_three', label='FieldThree')])
        input_four = dict(fields=[dict(id='field_four', label='FieldFour')])

        injector_one = dict(env=dict(EXTRA_VAR_FROM_FIELD_ONE='{{ field_one }}'))
        injector_two = dict(env=dict(EXTRA_VAR_FROM_FIELD_TWO='{{ field_two }}'))
        injector_three = dict(env=dict(EXTRA_VAR_FROM_FIELD_THREE='{{ field_three }}'))
        injector_four = dict(env=dict(EXTRA_VAR_FROM_FIELD_FOUR='{{ field_four }}'))

        desired_value = 'SomeDesiredValue'

        credentials = []
        for inp, inj in zip([input_one, input_two, input_three, input_four],
                            [injector_one, injector_two, injector_three, injector_four]):
            ct = factories.credential_type(inputs=inp, injectors=inj)
            credentials.append(factories.v2_credential(credential_type=ct,
                                                       inputs={inp['fields'][0]['id']: desired_value}))

        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='ansible_env.yml',
                                       ask_credential_on_launch=True)

        job = jt.launch(dict(extra_credentials=[cred.id for cred in credentials])).wait_until_completed()
        assert job.is_successful

        ansible_env = job.related.job_events.get(host=host.id, task='debug').results.pop().event_data.res.ansible_env
        for var in ('EXTRA_VAR_FROM_FIELD_ONE', 'EXTRA_VAR_FROM_FIELD_TWO',
                    'EXTRA_VAR_FROM_FIELD_THREE', 'EXTRA_VAR_FROM_FIELD_FOUR'):
            assert getattr(ansible_env, var) == desired_value

    def test_confirm_extra_credentials_injectors_are_sourced_with_vault_credentials(self, request, factories):
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='vaulted_ansible_env.yml')
        jt.vault_credential = factories.v2_credential(kind='vault', vault_password='tower').id

        cloud_credentials = [factories.v2_credential(kind=cred_type) for cred_type in ('aws', 'azure_rm', 'gce')]
        for cred in cloud_credentials:
            jt.add_extra_credential(cred)

        job = jt.launch().wait_until_completed()
        request.addfinalizer(job.delete)  # Noisy neighbor
        assert job.is_successful

        env_vars = ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AZURE_CLIENT_ID', 'AZURE_SECRET',
                    'AZURE_SUBSCRIPTION_ID', 'AZURE_TENANT', 'GCE_EMAIL', 'GCE_CREDENTIALS_FILE_PATH', 'GCE_PROJECT')

        for env_var in env_vars:
            assert env_var in job.job_env

        ansible_env = job.related.job_events.get(host=host.id, task='debug').results.pop().event_data.res.ansible_env

        for env_var in env_vars:
            assert env_var in ansible_env


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateRelatedCredentials(APITest):

    def test_add_machine_creds_check_backwards_compatibility(self, factories, v1, job_template_no_credential):
        jt = job_template_no_credential
        v1_jt_view = v1.job_templates.get(id=job_template_no_credential.id).results[0].get()
        cred = factories.credential()

        jt.add_credential(cred)
        jt.get()
        v1_jt_view.get()
        assert v1_jt_view.credential == cred.id
        assert v1_jt_view.vault_credential is None
        assert v1_jt_view.cloud_credential is None
        assert v1_jt_view.network_credential is None

        assert jt.credential == cred.id
        assert jt.vault_credential is None
        assert jt.related.extra_credentials.get().count == 0
        assert jt.related.credentials.get().results.pop().id == cred.id

        jt.remove_credential(cred)
        jt.get()
        v1_jt_view.get()
        assert v1_jt_view.credential is None
        assert v1_jt_view.vault_credential is None
        assert v1_jt_view.cloud_credential is None
        assert v1_jt_view.network_credential is None

        assert jt.credential is None
        assert jt.vault_credential is None
        assert jt.related.extra_credentials.get().count == 0
        assert jt.related.credentials.get().count == 0

    def test_add_vault_creds_check_backwards_compatibility(self, factories, v1, job_template_no_credential):
        jt = job_template_no_credential
        v1_jt_view = v1.job_templates.get(id=job_template_no_credential.id).results[0].get()
        cred = factories.v2_credential(kind='vault', vault_password='tower')

        jt.add_credential(cred)
        jt.get()
        v1_jt_view.get()
        assert v1_jt_view.credential is None
        assert v1_jt_view.vault_credential == cred.id
        assert v1_jt_view.cloud_credential is None
        assert v1_jt_view.network_credential is None

        assert jt.credential is None
        assert jt.vault_credential == cred.id
        assert jt.related.extra_credentials.get().count == 0
        assert jt.related.credentials.get().results.pop().id == cred.id

        jt.remove_credential(cred)
        jt.get()
        v1_jt_view.get()
        assert v1_jt_view.credential is None
        assert v1_jt_view.vault_credential is None
        assert v1_jt_view.cloud_credential is None
        assert v1_jt_view.network_credential is None

        assert jt.credential is None
        assert jt.vault_credential is None
        assert jt.related.extra_credentials.get().count == 0
        assert jt.related.credentials.get().count == 0

    def test_add_cloud_creds_check_backwards_compatibility(self, factories, v1, job_template_no_credential):
        jt = job_template_no_credential
        v1_jt_view = v1.job_templates.get(id=job_template_no_credential.id).results[0].get()
        creds = []
        for i in range(3):
            cred_type = factories.credential_type(kind='cloud')
            creds.append(factories.v2_credential(credential_type=cred_type))

        # remove after https://github.com/ansible/ansible-tower/issues/7935 is resolved
        creds = sorted(creds, key=lambda cred: cred.name, reverse=True)

        for cred in creds:
            jt.add_credential(cred)
        jt.get()
        v1_jt_view.get()
        assert v1_jt_view.credential is None
        assert v1_jt_view.vault_credential is None
        assert v1_jt_view.cloud_credential == creds[0].id
        assert v1_jt_view.network_credential is None

        assert jt.credential is None
        assert jt.vault_credential is None
        extra_creds = jt.related.extra_credentials.get().results
        assert set([cred.id for cred in extra_creds]) == set([cred.id for cred in creds])
        related_creds = jt.related.credentials.get().results
        assert set([cred.id for cred in related_creds]) == set([cred.id for cred in creds])

        for cred in creds:
            jt.remove_credential(cred)
        jt.get()
        v1_jt_view.get()
        assert v1_jt_view.credential is None
        assert v1_jt_view.vault_credential is None
        assert v1_jt_view.cloud_credential is None
        assert v1_jt_view.network_credential is None

        assert jt.credential is None
        assert jt.vault_credential is None
        assert jt.related.extra_credentials.get().count == 0
        assert jt.related.credentials.get().count == 0

    def test_add_network_creds_check_backwards_compatibility(self, factories, v1, job_template_no_credential):
        jt = job_template_no_credential
        v1_jt_view = v1.job_templates.get(id=job_template_no_credential.id).results[0].get()
        creds = []
        for i in range(3):
            cred_type = factories.credential_type(kind='net')
            creds.append(factories.v2_credential(credential_type=cred_type))

        # remove after https://github.com/ansible/ansible-tower/issues/7935 is resolved
        creds = sorted(creds, key=lambda cred: cred.name, reverse=True)

        for cred in creds:
            jt.add_credential(cred)
        jt.get()
        v1_jt_view.get()
        assert v1_jt_view.credential is None
        assert v1_jt_view.vault_credential is None
        assert v1_jt_view.cloud_credential is None
        assert v1_jt_view.network_credential == creds[0].id

        assert jt.credential is None
        assert jt.vault_credential is None
        extra_creds = jt.related.extra_credentials.get().results
        assert set([cred.id for cred in extra_creds]) == set([cred.id for cred in creds])
        related_creds = jt.related.credentials.get().results
        assert set([cred.id for cred in related_creds]) == set([cred.id for cred in creds])

        for cred in creds:
            jt.remove_credential(cred)
        jt.get()
        v1_jt_view.get()
        assert v1_jt_view.credential is None
        assert v1_jt_view.vault_credential is None
        assert v1_jt_view.cloud_credential is None
        assert v1_jt_view.network_credential is None

        assert jt.credential is None
        assert jt.vault_credential is None
        assert jt.related.extra_credentials.get().count == 0
        assert jt.related.credentials.get().count == 0

    def test_patch_machine_credential_check_related_credentials(self, factories):
        cred = factories.credential()
        jt = factories.v2_job_template(credential=None)
        jt.credential = cred.id

        related_creds = jt.related.credentials.get()
        assert related_creds.count == 1
        assert related_creds.results.pop().id == cred.id

        jt.credential = None
        related_creds = jt.related.credentials.get()
        assert jt.related.credentials.get().count == 0

    def test_patch_vault_credential_check_related_credentials(self, factories):
        cred = factories.v2_credential(kind='vault', vault_password='tower')
        jt = factories.v2_job_template(credential=None)
        jt.vault_credential = cred.id

        related_creds = jt.related.credentials.get()
        assert related_creds.count == 1
        assert related_creds.results.pop().id == cred.id

        jt.vault_credential = None
        related_creds = jt.related.credentials.get()
        assert jt.related.credentials.get().count == 0

    def test_patch_cloud_credential_check_related_credentials(self, factories, v2):
        cred_type = factories.credential_type(kind='cloud')
        cred = factories.v2_credential(credential_type=cred_type)
        jt = factories.job_template(credential=None)
        jt.cloud_credential = cred.id

        v2_jt_view = v2.job_templates.get(id=jt.id).results.pop()
        related_creds = v2_jt_view.related.credentials.get()
        assert related_creds.count == 1
        assert related_creds.results.pop().id == cred.id

        jt.cloud_credential = None
        related_creds = v2_jt_view.related.credentials.get()
        assert v2_jt_view.related.credentials.get().count == 0

    def test_patch_net_credential_check_related_credentials(self, factories, v2):
        cred_type = factories.credential_type(kind='net')
        cred = factories.v2_credential(credential_type=cred_type)
        jt = factories.job_template(credential=None)
        jt.network_credential = cred.id

        v2_jt_view = v2.job_templates.get(id=jt.id).results.pop()
        related_creds = v2_jt_view.related.credentials.get()
        assert related_creds.count == 1
        assert related_creds.results.pop().id == cred.id

        jt.network_credential = None
        related_creds = v2_jt_view.related.credentials.get()
        assert v2_jt_view.related.credentials.get().count == 0

    def test_add_extra_credentials_check_related_credentials(self, factories, custom_extra_credentials):
        jt = factories.v2_job_template(credential=None)
        for cred in custom_extra_credentials:
            jt.add_extra_credential(cred)

        related_creds = jt.related.credentials.get()
        assert related_creds.count == len(custom_extra_credentials)
        assert set([cred.id for cred in related_creds.results]) == set([cred.id for cred in custom_extra_credentials])

        for cred in custom_extra_credentials:
            jt.remove_extra_credential(cred)
        related_creds = jt.related.credentials.get()
        assert jt.related.credentials.get().count == 0
