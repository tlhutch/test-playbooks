import re

import base64
import fauxfactory
import pytest
import requests
from urllib.parse import urljoin

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from towerkit.config import config
from towerkit import utils
from kubernetes.stream import stream

from tests.api import APITest


@pytest.fixture(scope='class')
def k8s_conjur(gke_client_cscope, request):
    K8sClient = gke_client_cscope(config.credentials)
    prefix = 'conjur'
    cluster_domain = 'services.k8s.tower-qe.testing.ansible.com'
    deployment_name = K8sClient.random_deployment_name(prefix)
    containerspec = [{'name': '{}-{}'.format(deployment_name, 'app'),
                        'image': 'cyberark/conjur',
                        'ports': [{'containerPort': 80, 'protocol': 'TCP'}],
                        'env': [{'name': 'DATABASE_URL',
                                'value': 'postgres://postgres@{}/postgres'.format(deployment_name)},
                                {'name': 'CONJUR_DATA_KEY',
                                 'value': config.credentials.conjur.datakey}],
                        'command': ['conjurctl'],
                        'args': ['server']},
                     {'name': '{}-{}'.format(deployment_name, 'pg'),
                      'image': 'postgres:9.3',
                      'ports': [{'containerPort': 5432, 'protocol': 'TCP'}]}]
    portspec = [{'name': 'conjur',
                     'port': 80,
                     'protocol': 'TCP',
                     'targetPort': 80},
                     {'name': 'postgres',
                     'port': 5432,
                     'protocol': 'TCP',
                     'targetPort': 5432}]
    conjur_deployment = K8sClient.generate_deployment(deployment_name, containerspec)
    conjur_service = K8sClient.generate_service(deployment_name, portspec)
    K8sClient.apps.create_namespaced_deployment(body=conjur_deployment, namespace='default')
    K8sClient.core.create_namespaced_service(body=conjur_service, namespace='default')
    pod_name = K8sClient.core.list_namespaced_pod('default', label_selector='run={}'.format(deployment_name)).items[0].metadata.name
    request.addfinalizer(lambda: K8sClient.destroy(deployment_name))
    utils.logged_sleep(60) # Sleeping for conjur to initialize the database. This will happen only once for the class.
    api_key = None
    conjur_url = "https://http-{}-port-80.{}".format(deployment_name, cluster_domain)
    try:
        deploy_info = stream(K8sClient.core.connect_get_namespaced_pod_exec,
                             pod_name,
                             'default',
                             container='{}-app'.format(deployment_name),
                             command=['conjurctl', 'account', 'create', 'test'],
                             stderr=True,
                             stdin=False,
                             stdout=True,
                             tty=False)
        api_key = re.search(r'API key for admin: ([^\s]+)', deploy_info).group(1)
    except:
        pytest.skip('Unable to get API Key')

    def create_conjur_secrets(token, secret_id, var_value_tuples=[]):
        policy_body = '\n    - !variable '.join([v[0] for v in var_value_tuples])
        policy = '- !policy\n  id: {}\n  body:\n    - !variable {}'.format(secret_id, policy_body)
        path = urljoin(conjur_url, '/'.join([
            'policies', account, 'policy', 'root'
        ]))
        resp = requests.put(
            path,
            data=policy,
            headers={'Authorization': 'Token token="{}"'.format(token)}
        )
        resp.raise_for_status()
        for v in var_value_tuples:

            # set a secret variable value
            path = urljoin(conjur_url, '/'.join([
                'secrets', account, 'variable', '{}/{}'.format(secret_id, v[0])
            ]))
            resp = requests.post(
                path,
                data=v[1],
                headers={'Authorization': 'Token token="{}"'.format(token)}
            )
            resp.raise_for_status()
    try:
        account = 'test'
        username = 'admin'
        resp = requests.post(
            urljoin(conjur_url, '/'.join(['authn', account, username, 'authenticate'])),
            headers={'Content-Type': 'text/plain'},
            data=api_key
        )
        token = base64.b64encode(resp.content).decode('utf-8')
        resp.raise_for_status()
        create_conjur_secrets(token, 'super', var_value_tuples=[('secret', 'CLASSIFIED'),
                                                          ('vault_1', 'secret1'),
                                                          ('vault_2', 'secret2'),
                                                          ])

    except:
        pytest.skip('Unable to populate conjur')
    conjur_info = {'url': conjur_url, 'api_key': api_key}
    return conjur_info


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestConjurCredential(APITest):

    def create_conjur_credential(self, factories, v2, url, api_key, account, username):
        # create a credential w/ a conjur api_key
        cred_type = v2.credential_types.get(
            managed_by_tower=True,
            name='CyberArk Conjur Secret Lookup'
        ).results.pop()
        inputs = {
            'url': url,
            'api_key': api_key,
            'account': account,
            'username': username,
        }
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type,
            inputs=inputs
        )
        return v2.credentials.post(payload)

    def launch_job(self, factories, v2, path, secret_version=None,
                   url=None, api_key=None, account=None, username=None):

        conjur_credential = self.create_conjur_credential(factories, v2, url=url, api_key=api_key, account=account, username=username)

        # create an SSH credential
        cred_type = v2.credential_types.get(managed_by_tower=True, kind='ssh').results.pop()
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type
        )
        credential = v2.credentials.post(payload)

        # associate cred.username -> conjur_cred
        metadata = {
            'secret_path': path,
        }
        if secret_version:
            metadata['secret_version'] = secret_version
        credential.related.input_sources.post(dict(
            input_field_name='username',
            source_credential=conjur_credential.id,
            metadata=metadata
        ))

        # assign the SSH credential to a JT and run it
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='ping.yml',
                                       credential=credential)
        return jt.launch().wait_until_completed()

    @pytest.mark.parametrize('path, secret_version, expected', [
        ['super/secret', None, 'CLASSIFIED'],
        ['super/secret', '1', 'CLASSIFIED'],
    ])
    def test_conjur_secret_lookup(self, factories, v2, path, secret_version, expected, k8s_conjur):
        job = self.launch_job(factories, v2, path, secret_version, username='admin',
                              account='test', url=k8s_conjur['url'], api_key=k8s_conjur['api_key'])
        job.assert_successful()
        assert '-u {}'.format(expected) in ' '.join(job.job_args)

    def test_conjur_secret_bad_path(self, factories, v2, k8s_conjur):
        job = self.launch_job(factories, v2, 'super/missing', username='admin',
                              account='test', url=k8s_conjur['url'], api_key=k8s_conjur['api_key'])
        assert not job.is_successful
        assert 'requests.exceptions.HTTPError: 404 Client Error' in job.result_traceback

    def test_conjur_secret_bad_url(self, factories, v2, k8s_conjur):
        job = self.launch_job(factories, v2, '', url='http://missing.local:8200', api_key=k8s_conjur['api_key'])
        assert not job.is_successful
        assert 'Failed to establish a new connection: [Errno -2] Name or service not known' in job.result_traceback

    @pytest.mark.parametrize('api_key_permutations', [
        {'api_key': False, 'account': 'test', 'username': 'admin'},
        {'account': 'missing-account', 'username': 'admin', 'api_key': True},
        {'username': 'whodis', 'account': 'test', 'api_key': True}],
        ids=['wrong_key', 'wrong_account', 'wrong_user']
    )
    def test_conjur_secret_bad_api_key(self, factories, v2, k8s_conjur, api_key_permutations):
        if api_key_permutations['api_key']:
            api_key = k8s_conjur['api_key']
        else:
            api_key = "WRONG"
        job = self.launch_job(factories, v2, '', url=k8s_conjur['url'], api_key=api_key,
                              account=api_key_permutations['account'], username=api_key_permutations['username'])
        assert not job.is_successful
        assert 'requests.exceptions.HTTPError: 401 Client Error: Unauthorized' in job.result_traceback

    def test_conjur_secret_can_decrypt_ansible_vault(self, factories, v2, k8s_conjur):
        secrets = [('first', 'super/vault_1'), ('second', 'super/vault_2')]
        conjur_credential = self.create_conjur_credential(factories, v2, url=k8s_conjur['url'], api_key=k8s_conjur['api_key'], account='test', username='admin')
        jt = factories.v2_job_template(playbook='multivault.yml')
        for s in secrets:
            cred_type = v2.credential_types.get(managed_by_tower=True, kind='vault').results.pop()
            payload = factories.v2_credential.payload(
                name=fauxfactory.gen_utf8(),
                description=fauxfactory.gen_utf8(),
                credential_type=cred_type,
                inputs={'vault_id': s[0]}
            )
            credential = v2.credentials.post(payload)
            metadata = {
                'secret_path': s[1],
            }
            credential.related.input_sources.post(dict(
                input_field_name='vault_password',
                source_credential=conjur_credential.id,
                metadata=metadata
            ))
            jt.add_credential(credential)
        job = jt.launch().wait_until_completed()
        assert job.is_successful

    def test_conjur_custom_credential(self, factories, v2, k8s_conjur):
        conjur_credential = self.create_conjur_credential(factories, v2, url=k8s_conjur['url'], api_key=k8s_conjur['api_key'], account='test', username='admin')
        inputs = dict(fields=[dict(id='field_one', label='FieldOne', secret=True)])
        injectors = dict(extra_vars=dict(extra_var_from_field_one='{{ field_one }}'))
        credential_type = factories.credential_type(inputs=inputs, injectors=injectors)

        credential = factories.v2_credential(credential_type=credential_type)
        metadata = {
            'secret_path': 'super/secret',
        }
        credential.related.input_sources.post(dict(
            input_field_name='field_one',
            source_credential=conjur_credential.id,
            metadata=metadata
            ))
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_hostvars.yml')
        jt.add_extra_credential(credential)
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        hostvars = job.related.job_events.get(host=host.id, task='debug', event__startswith='runner_on_ok').results.pop().event_data.res.hostvars
        assert hostvars[host.name]['extra_var_from_field_one'] == 'CLASSIFIED'


@pytest.fixture(scope='class')
def k8s_vault(gke_client_cscope, request):
    K8sClient = gke_client_cscope(config.credentials)
    prefix = 'vault'
    deployment_name = K8sClient.random_deployment_name(prefix)
    cluster_domain = 'services.k8s.tower-qe.testing.ansible.com'
    containerspec = [{'name': 'vault',
                        'image': 'vault',
                        'ports': [{'containerPort': 1234, 'protocol': 'TCP'}],
                        'env': [{'name': 'VAULT_DEV_LISTEN_ADDRESS',
                                'value': '0.0.0.0:1234'},
                                {'name': 'VAULT_DEV_ROOT_TOKEN_ID',
                                 'value': config.credentials.hashivault.token}],
                        'securityContext': {'capabilities': {'add': ['IPC_LOCK']}}}]
    portspec = [{'name': 'vault',
                     'port': 1234,
                     'protocol': 'TCP',
                     'targetPort': 1234}]
    vault_deployment = K8sClient.generate_deployment(deployment_name, containerspec)
    vault_service = K8sClient.generate_service(deployment_name, portspec)
    K8sClient.apps.create_namespaced_deployment(body=vault_deployment, namespace='default')
    K8sClient.core.create_namespaced_service(body=vault_service, namespace='default')
    vault_url = "https://http-{}-port-1234.{}".format(deployment_name, cluster_domain)
    request.addfinalizer(lambda: K8sClient.destroy(deployment_name))

    sess = requests.Session()
    sess.headers['Authorization'] = 'Bearer {}'.format(config.credentials.hashivault.token)

    # if a secret engine mount exists at /kv, delete it
    sess.delete('{}/v1/sys/mounts/kv'.format(vault_url))
    # enable a v1 secret engine at path /kv
    sess.post('{}/v1/sys/mounts/kv'.format(vault_url), json={
        "type": "kv",
        "options": {"version": 1},
    })

    # if a secret engine mount exists at /versioned, delete it
    sess.delete('{}/v1/sys/mounts/versioned'.format(vault_url))
    # enable a v2 secret engine at path /versioned
    sess.post('{}/v1/sys/mounts/versioned'.format(vault_url), json={
        "type": "kv",
        "options": {"version": 2},
    })

    # add a v1 secret
    sess.post('{}/v1/kv/example-user'.format(vault_url), json={
        "username": "unversioned-username"
    })

    # add a few v2 secrets (an old and a new version)
    sess.post('{}/v1/versioned/data/example-user'.format(vault_url), json={
        "data": {
            "username": "old-username"
        }
    })
    sess.post('{}/v1/versioned/data/example-user'.format(vault_url), json={
        "data": {
            "username": "latest-username"
        }
    })
    sess.delete('{}/v1/sys/mounts/my-signer'.format(vault_url))
    # enable a secret engine at path /my-signer
    sess.post('{}/v1/sys/mounts/my-signer'.format(vault_url), json={
        "type": "ssh",
    })
    # generate a signing key
    sess.post('{}/v1/my-signer/config/ca'.format(vault_url), json={
        "generate_signing_key": True,
    })
    # generate a role
    sess.post('{}/v1/my-signer/roles/my-role'.format(vault_url), json={
        "allow_user_certificates": True,
        "allowed_users": "ec2-user",
        "default_extensions": [
            {"permit-pty": ""}
        ],
        "key_type": "ca",
        "default_user": "ec2-user",
        "ttl": "0m30s"
    })
    # read the generated public key
    resp = sess.get('{}/v1/my-signer/config/ca'.format(vault_url))

    # add ansible vault secrets
    secrets = [('vault_1', 'secret1'), ('vault_2', 'secret2')]
    for s in secrets:
        sess.post('{}/v1/kv/{}'.format(vault_url, s[0]), json={
            "password": s[1]
        })

    #
    # On a _managed host_ that we intend to SSH into, add the public_key
    # /etc/ssh/sshd_config
    # ...
    # TrustedUserCAKeys /etc/ssh/trusted-user-ca-keys.pem

    # ...and restart the SSH service.
    public_key = resp.json()['data']['public_key']  # noqa
    return vault_url


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestHashiCorpVaultCredentials(APITest):

    def create_hashicorp_vault_credential(self, factories, v2, url, token, api_version):
        cred_type = v2.credential_types.get(
            managed_by_tower=True,
            name='HashiCorp Vault Secret Lookup'
        ).results.pop()
        inputs = {
            'url': url,
            'token': token,
            'api_version': api_version
        }
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type,
            inputs=inputs
        )
        return v2.credentials.post(payload)

    def launch_job(self, factories, v2, api_version, secret_version, path, url=None,
                    token=config.credentials.hashivault.token, secret_key='username'):

        # create a credential w/ a hashicorp token
        cred_type = v2.credential_types.get(
            managed_by_tower=True,
            name='HashiCorp Vault Secret Lookup'
        ).results.pop()
        inputs = {
            'url': url,
            'token': token,
            'api_version': api_version
        }
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type,
            inputs=inputs
        )
        hashi_credential = self.create_hashicorp_vault_credential(factories, v2, url, token, api_version)

        # create an SSH credential
        cred_type = v2.credential_types.get(managed_by_tower=True, kind='ssh').results.pop()
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type
        )
        credential = v2.credentials.post(payload)

        # associate cred.username -> hashi_cred
        metadata = {
            'secret_path': path,
            'secret_key': secret_key,
        }
        if secret_version:
            metadata['secret_version'] = secret_version
        credential.related.input_sources.post(dict(
            input_field_name='username',
            source_credential=hashi_credential.id,
            metadata=metadata
        ))

        # assign the SSH credential to a JT and run it
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='ping.yml',
                                       credential=credential)
        return jt.launch().wait_until_completed()

    @pytest.mark.parametrize('api_version, secret_version, path, expected', [
        ['v1', None, '/kv/example-user/', 'unversioned-username'],
        ['v2', None, '/versioned/example-user', 'latest-username'],
        ['v2', '1', '/versioned/example-user', 'old-username'],
    ])
    def test_hashicorp_vault_kv_lookup(self, factories, v2, api_version,
                                       secret_version, path, expected, k8s_vault):
        """
        Verify that a v1 KV secret can be pulled from a Hashicorp Vault API
        and injected into an ansible-playbook run.

        This test assumes that you have a HashiCorp Vault API with a v1 K/V
        engine and a path of /kv/example-user/ that provides a value for the
        "username" key lookup

        This test also assumes that you have a HashiCorp Vault API with a v2
        (versioned) K/V engine and a path of /versioned/example-user/ that
        provides a versioned value for the "username" key lookup (with at least
        two versions)
        """
        job = self.launch_job(factories, v2, api_version, secret_version, path, url=k8s_vault)
        job.assert_successful()
        assert '-u {}'.format(expected) in ' '.join(job.job_args)

    @pytest.mark.parametrize('api_version', ['v1', 'v2'])
    @pytest.mark.parametrize('path', [
        '/missing/path',
        '/missing/',
        'a',
    ])
    def test_hashicorp_vault_kv_bad_path(self, factories, v2, api_version, path, k8s_vault):
        job = self.launch_job(factories, v2, api_version, None, path, url=k8s_vault)
        assert not job.is_successful
        assert 'requests.exceptions.HTTPError: 404 Client Error' in job.result_traceback

    @pytest.mark.parametrize('api_version, secret_version, path', [
        ['v1', None, '/kv/example-user/'],
        ['v2', None, '/versioned/example-user'],
        ['v2', '1', '/versioned/example-user'],
    ])
    def test_hashicorp_vault_kv_bad_key(self, factories, v2, api_version,
                                        secret_version, path, k8s_vault):
        job = self.launch_job(factories, v2, api_version, secret_version, path, url=k8s_vault,
                          secret_key='key-does-not-exist')
        assert not job.is_successful
        assert '{} is not present at {}'.format(
            'key-does-not-exist',
            path
        ) in job.result_traceback

    @pytest.mark.parametrize('api_version', ['v1', 'v2'])
    def test_hashicorp_vault_kv_bad_url(self, factories, v2, api_version):
        job = self.launch_job(factories, v2, api_version, None, '/any/path', url='http://missing.local:8200')
        assert not job.is_successful
        assert 'Failed to establish a new connection: [Errno -2] Name or service not known' in job.result_traceback

    @pytest.mark.parametrize('api_version', ['v1', 'v2'])
    def test_hashicorp_vault_kv_bad_token(self, factories, v2, api_version, k8s_vault):
        job = self.launch_job(factories, v2, api_version, None, '/any/path', url=k8s_vault,
                          token='totally-incorrect-token')
        assert not job.is_successful
        assert '403 Client Error: Forbidden' in job.result_traceback

    def test_hashicorp_vault_secret_can_decrypt_ansible_vault(self, factories, v2, k8s_vault):
        secrets = [('first', 'vault_1'), ('second', 'vault_2')]
        vault_credential = self.create_hashicorp_vault_credential(factories, v2, k8s_vault, config.credentials.hashivault.token, 'v1')
        jt = factories.v2_job_template(playbook='multivault.yml')
        for s in secrets:
            cred_type = v2.credential_types.get(managed_by_tower=True, kind='vault').results.pop()
            payload = factories.v2_credential.payload(
                name=fauxfactory.gen_utf8(),
                description=fauxfactory.gen_utf8(),
                credential_type=cred_type,
                inputs={'vault_id': s[0]}
            )
            credential = v2.credentials.post(payload)
            metadata = {
                'secret_path': s[1],
                'secret_key': 'password'
            }
            credential.related.input_sources.post(dict(
                input_field_name='vault_password',
                source_credential=vault_credential.id,
                metadata=metadata
            ))
            jt.add_credential(credential)
        job = jt.launch().wait_until_completed()
        assert job.is_successful

    def test_hashicorp_vault_custom_credential(self, factories, v2, k8s_vault):
        vault_credential = self.create_hashicorp_vault_credential(factories, v2, k8s_vault, config.credentials.hashivault.token, 'v1')
        inputs = dict(fields=[dict(id='field_one', label='FieldOne', secret=True)])
        injectors = dict(extra_vars=dict(extra_var_from_field_one='{{ field_one }}'))
        credential_type = factories.credential_type(inputs=inputs, injectors=injectors)

        credential = factories.v2_credential(credential_type=credential_type)
        metadata = {
            'secret_path': 'example-user',
            'secret_key': 'username'
        }
        credential.related.input_sources.post(dict(
            input_field_name='field_one',
            source_credential=vault_credential.id,
            metadata=metadata
            ))
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='debug_hostvars.yml')
        jt.add_extra_credential(credential)
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        hostvars = job.related.job_events.get(host=host.id, task='debug', event__startswith='runner_on_ok').results.pop().event_data.res.hostvars
        assert hostvars[host.name]['extra_var_from_field_one'] == 'CLASSIFIED'


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestHashiCorpSSHEngine(APITest):

    def launch_job(self, factories, v2, path, role, passphrase,
                   valid_principals=None, url=None, token=None):

        token = token or config.credentials.hashivault.token
        # create a credential w/ a hashicorp token
        cred_type = v2.credential_types.get(
            managed_by_tower=True,
            name='HashiCorp Vault Signed SSH'
        ).results.pop()
        inputs = {
            'url': url,
            'token': token,
        }
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type,
            inputs=inputs
        )
        hashi_credential = v2.credentials.post(payload)

        # create an keypair so the private half can be signed
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )
        cred_type = v2.credential_types.get(managed_by_tower=True, kind='ssh').results.pop()
        if passphrase is None:
            encryption = serialization.NoEncryption()
        else:
            encryption = serialization.BestAvailableEncryption(passphrase.encode('utf-8'))
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type,
            inputs={
                'ssh_key_data': key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=encryption
                ).decode('utf-8'),
                'ssh_key_unlock': passphrase or '',
            }
        )
        credential = v2.credentials.post(payload)

        # associate cred.username -> hashi_cred
        metadata = {
            'public_key': key.public_key().public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            ).decode('utf-8'),
            'secret_path': path,
            'role': role,
        }
        if valid_principals:
            metadata['valid_principals'] = valid_principals
        credential.related.input_sources.post(dict(
            input_field_name='ssh_public_key_data',
            source_credential=hashi_credential.id,
            metadata=metadata,
        ))

        # assign the SSH credential to a JT and run it
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='ping.yml',
                                       credential=credential)
        return jt.launch().wait_until_completed()

    @pytest.mark.parametrize('passphrase', [None, 'some-pass'])
    def test_hashicorp_ssh_signer(self, factories, v2, passphrase, k8s_vault):
        """
        Test support for https://www.vaultproject.io/docs/secrets/ssh/signed-ssh-certificates.html
        """
        job = self.launch_job(factories, v2, 'my-signer', 'my-role', passphrase, url=k8s_vault)
        job.assert_successful()
        assert re.search(
            'Identity added: /tmp/awx_[^/]+/credential_{}'.format(job.credential),
            job.result_stdout
        ) is not None, job.result_stdout
        assert re.search(
            'Certificate added: /tmp/awx_[^/]+/credential_{}-cert.pub'.format(job.credential),
            job.result_stdout
        ) is not None, job.result_stdout

    def test_hashicorp_ssh_signer_bad_path(self, factories, v2, k8s_vault):
        job = self.launch_job(factories, v2, 'missing-backend', 'foo', None, url=k8s_vault)
        assert job.is_successful is False
        assert 'requests.exceptions.HTTPError: 404 Client Error' in job.result_traceback

    def test_hashicorp_ssh_signer_restricted_user(self, factories, v2, k8s_vault):
        job = self.launch_job(factories, v2, 'my-signer', 'my-role', None,
                          valid_principals='root', url=k8s_vault)
        assert job.is_successful is False
        assert 'requests.exceptions.HTTPError: 400 Client Error' in job.result_traceback


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestAzureKVCredentials(APITest):

    def create_azurekv_credential(self, factories, v2, url):
        cred_type = v2.credential_types.get(
        managed_by_tower=True,
        name='Microsoft Azure Key Vault'
        ).results.pop()
        inputs = {
            'url': url,
            'client': config.credentials.cloud.azure.client_id,
            'secret': config.credentials.cloud.azure.secret,
            'tenant': config.credentials.cloud.azure.tenant,
        }
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type,
            inputs=inputs
        )
        return v2.credentials.post(payload)

    def launch_job(self, factories, v2, url, secret_field, version=None):
        azure_credential = self.create_azurekv_credential(factories, v2, 'https://qecredplugin.vault.azure.net/')

        # create an SSH credential
        cred_type = v2.credential_types.get(managed_by_tower=True, kind='ssh').results.pop()
        payload = factories.v2_credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=cred_type
        )
        credential = v2.credentials.post(payload)

        # associate cred.username -> azure_credential
        metadata = {
            'secret_field': secret_field,
        }
        if version:
            metadata['secret_version'] = version
        credential.related.input_sources.post(dict(
            input_field_name='username',
            source_credential=azure_credential.id,
            metadata=metadata,
        ))

        # assign the SSH credential to a JT and run it
        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='ping.yml',
                                       credential=credential)
        return jt.launch().wait_until_completed()

    @pytest.mark.parametrize('url, key, expected, version', [
        ['https://qecredplugin.vault.azure.net/', 'example-user', 'latest-username', None],
        ['https://qecredplugin.vault.azure.net/', 'example-user', 'from-azure',
         '74d97f8e2ce1470ba3bbd0f7407a75b4'],
    ])
    def test_azure_key_vault_lookup(self, factories, v2, url, key, expected, version):
        """
        Verify that a secret can be looked up from Azure Key Vault.

        This test assumes that you have an Azure Key Vault with a secret
        named `example-user` and a value of `from-azure`.
        """
        job = self.launch_job(factories, v2, url, key, version=version)
        job.assert_successful()
        assert '-u {}'.format(expected) in ' '.join(job.job_args)

    def test_azure_key_vault_bad_key(self, factories, v2):
        job = self.launch_job(factories, v2, 'https://qecredplugin.vault.azure.net/', 'missing-key')
        assert job.is_successful is False
        assert 'Secret not found: missing-key' in job.result_traceback

    def test_azure_key_vault_bad_version(self, factories, v2):
        job = self.launch_job(factories, v2,
                          'https://qecredplugin.vault.azure.net/', 'example-user',
                          'incorrect-version')
        assert job.is_successful is False
        assert 'KeyVaultErrorException' in job.result_traceback

    def test_azure_key_vault_cred_can_decrypt_ansible_vault(self, factories, v2):
        jt = factories.v2_job_template(playbook='multivault.yml')
        azure_credential = self.create_azurekv_credential(factories, v2, 'https://qecredplugin.vault.azure.net/')
        for s in [('first', 'vault1'), ('second', 'vault2')]:
            cred_type = v2.credential_types.get(managed_by_tower=True, kind='vault').results.pop()
            payload = factories.v2_credential.payload(
                name=fauxfactory.gen_utf8(),
                description=fauxfactory.gen_utf8(),
                credential_type=cred_type,
                inputs={'vault_id': s[0]}
            )
            credential = v2.credentials.post(payload)

            # associate cred.username -> azure_credential
            metadata = {
                'secret_field': s[1],
            }
            credential.related.input_sources.post(dict(
                input_field_name='vault_password',
                source_credential=azure_credential.id,
                metadata=metadata,
            ))
            jt.add_credential(credential)
        job = jt.launch().wait_until_completed()
        assert job.is_successful
