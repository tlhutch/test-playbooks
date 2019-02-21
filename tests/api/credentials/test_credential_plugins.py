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

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestConjurCredential(APITest):

    def setup_class(cls):
        if config.credentials.conjur.url is not None:
            url = config.credentials.conjur.url
            api_key = config.credentials.conjur.api_key
            account = config.credentials.conjur.account
            username = config.credentials.conjur.username

            # get an auth token
            resp = requests.post(
                urljoin(url, '/'.join(['authn', account, username, 'authenticate'])),
                headers={'Content-Type': 'text/plain'},
                data=api_key
            )
            token = base64.b64encode(resp.content).decode('utf-8')
            resp.raise_for_status()

            # set a variable policy
            policy = '- !policy\n  id: super\n  body:\n    - !variable secret'
            path = urljoin(url, '/'.join([
                'policies', account, 'policy', 'root'
            ]))
            resp = requests.put(
                path,
                data=policy,
                headers={'Authorization': 'Token token="{}"'.format(token)}
            )
            resp.raise_for_status()

            # set a secret variable value
            path = urljoin(url, '/'.join([
                'secrets', account, 'variable', 'super/secret'
            ]))
            resp = requests.post(
                path,
                data='CLASSIFIED',
                headers={'Authorization': 'Token token="{}"'.format(token)}
            )
            resp.raise_for_status()

    def launch_job(self, factories, v2, path, secret_version=None,
                   url=None, api_key=None, account=None, username=None):
        try:
            config.credentials.conjur.url is not None
        except Exception:
            pytest.skip('no conjur creds configured')

        url = url or config.credentials.conjur.url
        api_key = api_key or config.credentials.conjur.api_key
        account = account or config.credentials.conjur.account
        username = username or config.credentials.conjur.username
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
        conjur_credential = v2.credentials.post(payload)

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
    def test_conjur_secret_lookup(self, factories, v2, path, secret_version, expected):
        job = self.launch_job(factories, v2, path, secret_version)
        job.assert_successful()
        assert '-u {}'.format(expected) in ' '.join(job.job_args)

    def test_conjur_secret_bad_path(self, factories, v2):
        job = self.launch_job(factories, v2, 'super/missing')
        assert not job.is_successful
        assert 'requests.exceptions.HTTPError: 404 Client Error' in job.result_traceback

    def test_conjur_secret_bad_url(self, factories, v2):
        job = self.launch_job(factories, v2, '', url='http://missing.local:8200')
        assert not job.is_successful
        assert 'Failed to establish a new connection: [Errno -2] Name or service not known' in job.result_traceback

    @pytest.mark.parametrize('kwargs', [
        {'api_key': 'WRONG'},
        {'account': 'missing-account'},
        {'username': 'whodis'},
    ])
    def test_conjur_secret_bad_api_key(self, factories, v2, kwargs):
        job = self.launch_job(factories, v2, '', **kwargs)
        assert not job.is_successful
        assert 'requests.exceptions.HTTPError: 401 Client Error: Unauthorized' in job.result_traceback


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestHashiCorpVaultCredentials(APITest):

    def setup_class(cls):
        if config.credentials.hashivault.url is not None:
            host = config.credentials.hashivault.url
            sess = requests.Session()
            sess.headers['Authorization'] = 'Bearer {}'.format(config.credentials.hashivault.token)

            # if a secret engine mount exists at /kv, delete it
            sess.delete('{}/v1/sys/mounts/kv'.format(host))
            # enable a v1 secret engine at path /kv
            sess.post('{}/v1/sys/mounts/kv'.format(host), json={
                "type": "kv",
                "options": {"version": 1},
            })

            # if a secret engine mount exists at /versioned, delete it
            sess.delete('{}/v1/sys/mounts/versioned'.format(host))
            # enable a v2 secret engine at path /versioned
            sess.post('{}/v1/sys/mounts/versioned'.format(host), json={
                "type": "kv",
                "options": {"version": 2},
            })

            # add a v1 secret
            sess.post('{}/v1/kv/example-user'.format(host), json={
                "username": "unversioned-username"
            })

            # add a few v2 secrets (an old and a new version)
            sess.post('{}/v1/versioned/data/example-user'.format(host), json={
                "data": {
                    "username": "old-username"
                }
            })
            sess.post('{}/v1/versioned/data/example-user'.format(host), json={
                "data": {
                    "username": "latest-username"
                }
            })

    def launch_job(self, factories, v2, api_version, secret_version, path,
                   url=None, token=None, secret_key='username'):
        try:
            config.credentials.hashivault.url is not None
        except Exception:
            pytest.skip('no hashivault creds configured')

        url = url or config.credentials.hashivault.url
        token = token or config.credentials.hashivault.token
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
        hashi_credential = v2.credentials.post(payload)

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
                                       secret_version, path, expected):
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
        job = self.launch_job(factories, v2, api_version, secret_version, path)
        job.assert_successful()
        assert '-u {}'.format(expected) in ' '.join(job.job_args)

    @pytest.mark.parametrize('api_version', ['v1', 'v2'])
    @pytest.mark.parametrize('path', [
        '/missing/path',
        '/missing/',
        'a',
    ])
    def test_hashicorp_vault_kv_bad_path(self, factories, v2, api_version, path):
        job = self.launch_job(factories, v2, api_version, None, path)
        assert not job.is_successful
        assert 'requests.exceptions.HTTPError: 404 Client Error' in job.result_traceback

    @pytest.mark.parametrize('api_version, secret_version, path', [
        ['v1', None, '/kv/example-user/'],
        ['v2', None, '/versioned/example-user'],
        ['v2', '1', '/versioned/example-user'],
    ])
    def test_hashicorp_vault_kv_bad_key(self, factories, v2, api_version,
                                        secret_version, path):
        job = self.launch_job(factories, v2, api_version, secret_version, path,
                          secret_key='key-does-not-exist')
        assert not job.is_successful
        assert '{} is not present at {}'.format(
            'key-does-not-exist',
            path
        ) in job.result_traceback

    @pytest.mark.parametrize('api_version', ['v1', 'v2'])
    def test_hashicorp_vault_kv_bad_url(self, factories, v2, api_version):
        job = self.launch_job(factories, v2, api_version, None, '/any/path',
                          url='http://missing.local:8200')
        assert not job.is_successful
        assert 'Failed to establish a new connection: [Errno -2] Name or service not known' in job.result_traceback

    @pytest.mark.parametrize('api_version', ['v1', 'v2'])
    def test_hashicorp_vault_kv_bad_token(self, factories, v2, api_version):
        job = self.launch_job(factories, v2, api_version, None, '/any/path',
                          token='totally-incorrect-token')
        assert not job.is_successful
        assert '403 Client Error: Forbidden' in job.result_traceback


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestHashiCorpSSHEngine(APITest):

    def setup_class(cls):
        if config.credentials.hashivault.url is not None:
            host = config.credentials.hashivault.url
            sess = requests.Session()
            sess.headers['Authorization'] = 'Bearer {}'.format(config.credentials.hashivault.token)

            # if an ssh engine mount exists at /my-signer, delete it
            sess.delete('{}/v1/sys/mounts/my-signer'.format(host))
            # enable a secret engine at path /my-signer
            sess.post('{}/v1/sys/mounts/my-signer'.format(host), json={
                "type": "ssh",
            })
            # generate a signing key
            sess.post('{}/v1/my-signer/config/ca'.format(host), json={
                "generate_signing_key": True,
            })
            # generate a role
            sess.post('{}/v1/my-signer/roles/my-role'.format(host), json={
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
            resp = sess.get('{}/v1/my-signer/config/ca'.format(host))

            #
            # On a _managed host_ that we intend to SSH into, add the public_key
            # /etc/ssh/sshd_config
            # ...
            # TrustedUserCAKeys /etc/ssh/trusted-user-ca-keys.pem

            # ...and restart the SSH service.
            public_key = resp.json()['data']['public_key']  # noqa

    def launch_job(self, factories, v2, path, role, passphrase,
                   valid_principals=None, url=None, token=None):
        try:
            config.credentials.hashivault.url is not None
        except Exception:
            pytest.skip('no hashivault creds configured')

        url = url or config.credentials.hashivault.url
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
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
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
    def test_hashicorp_ssh_signer(self, factories, v2, passphrase):
        """
        Test support for https://www.vaultproject.io/docs/secrets/ssh/signed-ssh-certificates.html
        """
        job = self.launch_job(factories, v2, 'my-signer', 'my-role', passphrase)
        job.assert_successful()
        assert re.search(
            'Identity added: /tmp/awx_[^/]+/credential_{}'.format(job.credential),
            job.result_stdout
        ) is not None, job.result_stdout
        assert re.search(
            'Certificate added: /tmp/awx_[^/]+/credential_{}-cert.pub'.format(job.credential),
            job.result_stdout
        ) is not None, job.result_stdout

    def test_hashicorp_ssh_signer_bad_path(self, factories, v2):
        job = self.launch_job(factories, v2, 'missing-backend', 'foo', None)
        assert job.is_successful is False
        assert 'requests.exceptions.HTTPError: 404 Client Error' in job.result_traceback

    def test_hashicorp_ssh_signer_restricted_user(self, factories, v2):
        job = self.launch_job(factories, v2, 'my-signer', 'my-role', None,
                          valid_principals='root')
        assert job.is_successful is False
        assert 'requests.exceptions.HTTPError: 400 Client Error' in job.result_traceback


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestAzureKVCredentials(APITest):

    def launch_job(self, factories, v2, url, secret_field, version=None):
        # create a credential w/ a azure creds
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
        azure_credential = v2.credentials.post(payload)

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
