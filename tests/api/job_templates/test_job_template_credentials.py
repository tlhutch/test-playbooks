from distutils.version import LooseVersion
import logging
import six

import awxkit.exceptions as exc
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateCredentials(APITest):

    def test_job_template_creation_without_credential(self, factories):
        jt = factories.job_template()
        jt.remove_all_credentials()

    def test_job_template_cannot_have_multiple_same_type(self, factories):
        ct = factories.credential_type()
        cred1 = factories.credential(credential_type=ct)
        cred2 = factories.credential(credential_type=ct)
        assert cred1.credential_type == cred2.credential_type

        jt = factories.job_template(credential=None)
        jt.add_credential(cred1)
        with pytest.raises(exc.BadRequest) as e:
            jt.add_credential(cred2)
        assert e.value.msg['error'] == six.text_type(
            'Cannot assign multiple {} credentials.'
        ).format(ct.name)


@pytest.mark.ansible(host_pattern='tower[0]')  # assuming all nodes have same ssh installed
@pytest.mark.usefixtures('authtoken')
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
        job.assert_successful()
        assert job.get_related('credentials').count == 0

        job_template_no_credential.ask_credential_on_launch = True
        job = job_template_no_credential.launch().wait_until_completed()
        job.assert_successful()
        assert job.get_related('credentials').count == 0

    def test_launch_with_linked_credential(self, job_template_prompt_for_credential, ssh_credential):
        """Verify the job template launch endpoint requires user input when using a linked credential and
        `ask_credential_on_launch`.
        """
        job_template_prompt_for_credential.add_credential(ssh_credential)
        launch = job_template_prompt_for_credential.related.launch.get()

        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert not launch.credential_needed_to_start

        job = job_template_prompt_for_credential.launch().wait_until_completed()

        job.assert_successful()
        assert [c.id for c in job.get_related('credentials').results] == [ssh_credential.id]

    @pytest.mark.ansible_integration
    def test_launch_with_unencrypted_ssh_credential(self, skip_if_openshift, ansible_runner, job_template,
                                                    unencrypted_ssh_credential_with_ssh_key_data):
        (credential_type, credential) = unencrypted_ssh_credential_with_ssh_key_data

        job_template.remove_all_credentials()
        job_template.add_credential(credential)

        launch = job_template.related.launch.get()
        assert not launch.passwords_needed_to_start

        job = job_template.launch().wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "unencrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(list(contacted.values())[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                job.assert_successful()
            else:
                assert job.status == 'error'
                runtime_error = "RuntimeError: It looks like you're trying to use a private key in OpenSSH format"
                assert runtime_error in job.result_traceback
        else:
            job.assert_successful()

    @pytest.mark.ansible_integration
    def test_launch_with_encrypted_ssh_credential(self, skip_if_openshift, ansible_runner, job_template,
                                                  encrypted_ssh_credential_with_ssh_key_data):
        (credential_type, credential) = encrypted_ssh_credential_with_ssh_key_data

        job_template.remove_all_credentials()
        job_template.add_credential(credential)

        launch = job_template.get_related('launch')
        assert launch.passwords_needed_to_start == ['ssh_key_unlock']

        job = job_template.launch(dict(ssh_key_unlock='fo0m4nchU'))
        job.wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "encrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(list(contacted.values())[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                job.assert_successful()
            else:
                assert job.status == 'error'
                runtime_error = "RuntimeError: It looks like you're trying to use a private key in OpenSSH format"
                assert runtime_error in job.result_traceback
        else:
            job.assert_successful()

    @pytest.mark.ansible_integration
    def test_launch_with_bad_become_plugin(self, factories, ansible_version_cmp):
        cred = factories.credential(kind='ssh', become_method='foobar')
        jt = factories.job_template(credential=cred, playbook='become.yml')

        job = jt.launch().wait_until_completed()

        assert job.status == 'failed'
        if ansible_version_cmp('2.8.0') < 0:
            playbook_error = "option --become-method: invalid choice: u'foobar'"
        else:
            playbook_error = "Invalid become method specified, could not find matching plugin: 'foobar'"
        assert playbook_error in job.result_stdout, job.result_stdout

    @pytest.mark.ansible_integration
    def test_launch_with_no_become_plugin(self, factories, ansible_version_cmp):
        """Ensure sudo is used when no become plugin is specified."""

        cred = factories.credential(kind='ssh')
        jt = factories.job_template(credential=cred, playbook='become.yml')
        job = jt.launch().wait_until_completed()
        assert ' --become ' not in job.job_args[0]
        assert 'sudo' in job.result_stdout, job.result_stdout

    @pytest.mark.parametrize('become_plugin', ['doas', 'enable', 'ksu', 'pbrun', 'pmrun', 'runas', 'sesu', 'su', 'sudo'])
    @pytest.mark.ansible_integration
    def test_launch_with_ansible_shipped_become_plugin(self, skip_if_pre_ansible28, factories, become_plugin):
        """Ensure ansible built-in become plugins can be used."""

        cred = factories.credential(kind='ssh', become_method=become_plugin)
        jt = factories.job_template(credential=cred, playbook='become.yml')
        job = jt.launch().wait_until_completed()
        playbook_error = "Invalid become method specified, could not find matching plugin: '%s'" % become_plugin

        assert playbook_error not in job.result_stdout, job.result_stdout

    @pytest.mark.ansible_integration
    def test_launch_with_custom_become_plugin(self, skip_if_pre_ansible28, factories):
        """Ensure custom become plugins can be used."""

        cred = factories.credential(kind='ssh', become_method='custom_plugin', become_username='awx')
        jt = factories.job_template(credential=cred, playbook='become.yml')
        job = jt.launch().wait_until_completed()
        job.assert_successful()

    @pytest.mark.yolo
    def test_launch_with_multiple_credentials(self, v2, factories, custom_cloud_credentials, custom_network_credentials):
        machine_cred = factories.credential()
        vault_cred1 = factories.credential(kind='vault', vault_password='tower', vault_id='vault1')
        vault_cred2 = factories.credential(kind='vault', vault_password='tower', vault_id='vault2')

        creds = [machine_cred, vault_cred1, vault_cred2]
        creds.extend([c for c in custom_cloud_credentials])
        creds.extend([c for c in custom_network_credentials])
        jt = factories.job_template(credential=None, ask_credential_on_launch=True)
        jt.ds.inventory.add_host()
        job = jt.launch(dict(credentials=[c.id for c in creds]))
        job.wait_until_completed().assert_successful()

        job_creds = job.related.credentials.get().results
        assert set(c.id for c in job_creds) == set(c.id for c in creds)
        assert len(job_creds) == len(creds)

    def test_launch_with_multiple_credentials_but_ask_credential_on_launch_false(self, v2, factories,
                                                                                 custom_cloud_credentials,
                                                                                 custom_network_credentials):
        machine_cred = factories.credential()
        vault_cred1 = factories.credential(kind='vault', vault_password='tower', vault_id='vault1')
        vault_cred2 = factories.credential(kind='vault', vault_password='tower', vault_id='vault2')

        creds = [machine_cred, vault_cred1, vault_cred2]
        creds.extend([c for c in custom_cloud_credentials])
        creds.extend([c for c in custom_network_credentials])
        jt = factories.job_template(credential=None)
        jt.ds.inventory.add_host()
        job = jt.launch(dict(credentials=[c.id for c in creds]))
        job.wait_until_completed().assert_successful()
        assert job.related.credentials.get().count == 0

    @pytest.mark.yolo
    def test_provide_additional_vault_credential_on_launch(self, v2, factories):
        jt = factories.job_template(credential=None, ask_credential_on_launch=True)
        jt.ds.inventory.add_host()

        vault_cred1 = factories.credential(kind='vault', vault_password='tower', vault_id='vault1')
        vault_cred2 = factories.credential(kind='vault', vault_password='tower', vault_id='vault2')
        jt.add_credential(vault_cred1)

        with pytest.raises(exc.BadRequest) as e:
            jt.launch(dict(credentials=[vault_cred2.id]))
        error_msg = ('Removing Vault (id={0.inputs.vault_id}) credential at launch time without replacement '
                     'is not supported. Provided list lacked credential(s): {0.name}-{0.id}.').format(vault_cred1)
        assert e.value.msg == {'credentials': [error_msg]}

        job = jt.launch(dict(credentials=[vault_cred1.id, vault_cred2.id]))
        job.wait_until_completed().assert_successful()

        job_creds = job.related.credentials.get().results
        assert set(c.id for c in job_creds) == set([vault_cred1.id, vault_cred2.id])
        assert job.related.credentials.get().count == 2


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateVaultCredentials(APITest):

    @pytest.mark.parametrize('v, cred_args', [['v2', dict(kind='vault', vault_password='tower')]])
    def test_decrypt_vaulted_playbook_with_vault_credential(self, factories, v, cred_args):
        host_factory = factories.host
        cred_factory = factories.credential
        jt_factory = factories.job_template

        host = host_factory()
        jt = jt_factory(inventory=host.ds.inventory, playbook='vaulted_debug_hostvars.yml')

        vault_cred = cred_factory(**cred_args)
        jt.add_credential(vault_cred)

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        debug_tasks = job.related.job_events.get(host_name=host.name, task='debug', event__startswith='runner_on_ok').results
        assert len(debug_tasks) == 1
        assert list(debug_tasks[0].event_data.res.hostvars.keys()) == [host.name]

    def test_decrypt_vaulted_playbook_with_lone_ask_on_launch_vault_credential(self, factories):
        cred_args = dict(kind='vault', vault_password='ASK')
        host_factory = factories.host
        cred_factory = factories.credential
        jt_factory = factories.job_template

        host = host_factory()
        vault_cred = cred_factory(**cred_args)
        jt = jt_factory(inventory=host.ds.inventory, playbook='vaulted_debug_hostvars.yml')
        jt.remove_all_credentials()
        jt.add_credential(vault_cred)

        with pytest.raises(exc.BadRequest) as e:
            jt.launch().wait_until_completed()
        assert e.value.msg == {'passwords_needed_to_start': ['vault_password']}

        job = jt.launch(dict(vault_password='tower')).wait_until_completed()
        job.assert_successful()

        debug_tasks = job.related.job_events.get(host_name=host.name, task='debug', event__startswith='runner_on_ok').results
        assert len(debug_tasks) == 1
        assert list(debug_tasks[0].event_data.res.hostvars.keys()) == [host.name]

    def test_decrypt_vaulted_playbook_with_multiple_vault_credentials(self, factories):
        host = factories.host()
        jt = factories.job_template(
            inventory=host.ds.inventory,
            playbook='multivault.yml',
            extra_vars='{"with_dotted": 1}'
        )

        vault_cred1 = factories.credential(kind='vault', vault_password='secret1', vault_id='first')
        vault_cred2 = factories.credential(kind='vault', vault_password='secret2', vault_id='second')
        vault_cred3 = factories.credential(kind='vault', vault_password='secret3', vault_id='dotted.id')
        jt.add_credential(vault_cred1)
        jt.add_credential(vault_cred2)
        jt.add_credential(vault_cred3)

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        debug_tasks = job.related.job_events.get(host_name=host.name, task='debug', event__startswith='runner_on_ok').results
        assert len(debug_tasks) == 3
        assert any('First!' in task.stdout for task in debug_tasks)
        assert any('Second!' in task.stdout for task in debug_tasks)
        assert any('Dotted!' in task.stdout for task in debug_tasks)

    @pytest.mark.yolo
    def test_decrypt_vaulted_playbook_with_multiple_ask_on_launch_vault_credentials(self, factories):
        host = factories.host()
        jt = factories.job_template(
            inventory=host.ds.inventory,
            playbook='multivault.yml',
            extra_vars='{"with_dotted": 1}'
        )

        vault_cred1 = factories.credential(kind='vault', vault_password='ASK', vault_id='first')
        vault_cred2 = factories.credential(kind='vault', vault_password='ASK', vault_id='second')
        vault_cred3 = factories.credential(kind='vault', vault_password='ASK', vault_id='dotted.id')
        jt.add_credential(vault_cred1)
        jt.add_credential(vault_cred2)
        jt.add_credential(vault_cred3)

        with pytest.raises(exc.BadRequest) as e:
            jt.launch().wait_until_completed()
        assert set(e.value.msg['passwords_needed_to_start']) == set([
            'vault_password.first',
            'vault_password.second',
            'vault_password.dotted.id'
        ])
        assert len(e.value.msg['passwords_needed_to_start']) == 3

        payload = {'vault_password.first': 'secret1',
                   'vault_password.second': 'secret2',
                   'vault_password.dotted.id': 'secret3'}

        job = jt.launch(payload).wait_until_completed()
        job.assert_successful()

        debug_tasks = job.related.job_events.get(host_name=host.name, task='debug', event__startswith='runner_on_ok').results
        assert len(debug_tasks) == 3
        assert any('First!' in task.stdout for task in debug_tasks)
        assert any('Second!' in task.stdout for task in debug_tasks)
        assert any('Dotted!' in task.stdout for task in debug_tasks)

    def test_cannot_assign_multiple_vault_credentials_with_same_vault_id(self, factories):
        jt = factories.job_template()
        vault_cred1 = factories.credential(kind='vault', vault_password='secret1', vault_id='foo')
        vault_cred2 = factories.credential(kind='vault', vault_password='secret2', vault_id='foo')
        jt.add_credential(vault_cred1)
        with pytest.raises(exc.BadRequest) as e:
            jt.add_credential(vault_cred2)
        assert e.value.msg == {'error': 'Cannot assign multiple Vault (id=foo) credentials.'}


@pytest.fixture(scope='class')
def custom_cloud_credentials(class_factories):
    cred_types = [class_factories.credential_type(kind='cloud') for _ in range(3)]
    return [class_factories.credential(credential_type=cred_type) for cred_type in cred_types]


@pytest.fixture(scope='class')
def custom_network_credentials(class_factories):
    cred_types = [class_factories.credential_type(kind='net') for _ in range(3)]
    return [class_factories.credential(credential_type=cred_type) for cred_type in cred_types]


@pytest.fixture(scope='class', params=('custom_cloud_credentials', 'custom_network_credentials'))
def custom_extra_credentials(request):
    return request.getfixturevalue(request.param)


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateExtraCredentials(APITest):

    def test_job_template_with_added_and_removed_custom_extra_credentials(self, factories, custom_extra_credentials):
        ssh_cred = factories.credential()
        jt = factories.job_template(credential=ssh_cred)

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
        jt = factories.job_template()
        scm_cred = factories.credential(kind='scm')
        ssh_cred = factories.credential()
        vault_cred = factories.credential(kind='vault', inputs=dict(vault_password='fake'))

        for cred in (scm_cred, ssh_cred, vault_cred):
            with pytest.raises(exc.BadRequest) as e:
                jt.add_extra_credential(cred)
                assert e.value.msg == {'error': 'Extra credentials must be network or cloud.'}
            assert not jt.related.extra_credentials.get().results

    @pytest.fixture(scope='class')
    def job_template(self, class_factories):
        return class_factories.job_template()

    @pytest.mark.parametrize('credential_kind, kind_name',
                             [('aws', 'Amazon Web Services'),
                              ('gce', 'Google Compute Engine'),
                              ('azure_rm', 'Microsoft Azure Resource Manager'),
                              ('net', 'Network'),
                              ('openstack', 'OpenStack'),
                              ('cloudforms', 'Red Hat CloudForms'),
                              ('satellite6', 'Red Hat Satellite 6'),
                              ('vmware', 'VMware vCenter')])
    def test_confirm_only_single_managed_by_tower_extra_credential_allowed(self, factories, job_template,
                                                                           credential_kind, kind_name):
        cred_one, cred_two = [factories.credential(kind=credential_kind) for _ in range(2)]

        job_template.add_extra_credential(cred_one)

        with pytest.raises(exc.BadRequest) as e:
            job_template.add_extra_credential(cred_two)
        assert e.value.msg == {'error': 'Cannot assign multiple {} credentials.'.format(kind_name)}

        assert cred_two.id not in [c.id for c in job_template.related.extra_credentials.get().results]

        job_template.remove_extra_credential(cred_one)
        assert cred_one.id not in [c.id for c in job_template.related.extra_credentials.get().results]

        job_template.add_extra_credential(cred_two)
        assert cred_two.id in [c.id for c in job_template.related.extra_credentials.get().results]

    def test_confirm_extra_credentials_injectors_are_sourced(self, request, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='ansible_env.yml')

        cloud_credentials = [factories.credential(kind=cred_type) for cred_type in ('aws', 'gce')]
        cloud_credentials.append(factories.credential(kind='azure_rm', cloud_environment='SomeEnvironment'))
        for cred in cloud_credentials:
            jt.add_extra_credential(cred)

        job = jt.launch().wait_until_completed()
        request.addfinalizer(job.delete)  # Noisy neighbor

        job.assert_successful()

        env_vars = ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AZURE_CLIENT_ID', 'AZURE_CLOUD_ENVIRONMENT', 'AZURE_SECRET',
                    'AZURE_SUBSCRIPTION_ID', 'AZURE_TENANT', 'GCE_EMAIL', 'GCE_CREDENTIALS_FILE_PATH', 'GCE_PROJECT')

        for env_var in env_vars:
            assert env_var in job.job_env

        ansible_env = job.related.job_events.get(host=host.id, task='debug', event__startswith='runner_on_ok').results.pop().event_data.res.ansible_env

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
            credentials.append(factories.credential(credential_type=ct,
                                                       inputs={inp['fields'][0]['id']: desired_value}))

        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='ansible_env.yml',
                                       ask_credential_on_launch=True)

        job = jt.launch(dict(extra_credentials=[cred.id for cred in credentials])).wait_until_completed()
        job.assert_successful()

        runner_on_ok_events = job.related.job_events.get(host=host.id, task='debug', event__startswith='runner_on_ok').results
        assert len(runner_on_ok_events) > 0, f"No events found! Only found {job.related.job_events.get(host=host.id, task='debug')}"
        ansible_env = runner_on_ok_events.pop().event_data.res.ansible_env
        for var in ('EXTRA_VAR_FROM_FIELD_ONE', 'EXTRA_VAR_FROM_FIELD_TWO',
                    'EXTRA_VAR_FROM_FIELD_THREE', 'EXTRA_VAR_FROM_FIELD_FOUR'):
            assert getattr(ansible_env, var) == desired_value

    def test_confirm_extra_credentials_injectors_are_sourced_with_vault_credentials(self, request, factories):
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='vaulted_ansible_env.yml')
        jt.add_credential(factories.credential(kind='vault', vault_password='tower'))

        cloud_credentials = [factories.credential(kind=cred_type) for cred_type in ('aws', 'azure_rm', 'gce')]
        for cred in cloud_credentials:
            jt.add_extra_credential(cred)

        job = jt.launch().wait_until_completed()
        request.addfinalizer(job.delete)  # Noisy neighbor
        job.assert_successful()

        env_vars = ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AZURE_CLIENT_ID', 'AZURE_SECRET',
                    'AZURE_SUBSCRIPTION_ID', 'AZURE_TENANT', 'GCE_EMAIL', 'GCE_CREDENTIALS_FILE_PATH', 'GCE_PROJECT')

        for env_var in env_vars:
            assert env_var in job.job_env

        ansible_env = job.related.job_events.get(host=host.id, task='debug', event__startswith='runner_on_ok').results.pop().event_data.res.ansible_env

        for env_var in env_vars:
            assert env_var in ansible_env


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateRelatedCredentials(APITest):

    def test_add_extra_credentials_check_related_credentials(self, factories, custom_extra_credentials):
        jt = factories.job_template(credential=None)
        for cred in custom_extra_credentials:
            jt.add_extra_credential(cred)

        related_creds = jt.related.credentials.get()
        assert related_creds.count == len(custom_extra_credentials)
        assert set([cred.id for cred in related_creds.results]) == set([cred.id for cred in custom_extra_credentials])

        for cred in custom_extra_credentials:
            jt.remove_extra_credential(cred)
        related_creds = jt.related.credentials.get()
        assert jt.related.credentials.get().count == 0
