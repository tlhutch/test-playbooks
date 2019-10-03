import os

from awxkit.config import config
from awxkit import utils
import fauxfactory
import requests
import pytest


fixtures_dir = os.path.dirname(__file__)


# SSH machine credentials
@pytest.fixture(scope="function")
def ssh_credential(admin_user, factories):
    cred = factories.credential(description="machine (ssh) credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=None, become_password=None, organization=None)
    return cred


@pytest.fixture(scope="function")
def another_ssh_credential(admin_user, factories):
    cred = factories.credential(description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=None, become_password=None)
    return cred


@pytest.fixture(scope="function")
def ssh_credential_ask(admin_user, factories):
    """Create ssh credential with 'ASK' password"""
    cred = factories.credential(description="machine credential with ASK password - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, password='ASK', become_password=None,
                                ssh_key_data=None)
    return cred


@pytest.fixture(scope="function")
def ssh_credential_with_ssh_key_data_and_sudo(ansible_adhoc, admin_user, factories):
    """Create ssh credential with sudo user from ansible facts"""
    # FIXME: should get facts from managed host
    # managed host is unreachable, but will almost always be same as other nodes
    ansible_facts = getattr(ansible_adhoc(), 'tower[0]').setup()
    sudo_user = list(ansible_facts.values())[0]['ansible_facts']['ansible_env'].get('SUDO_USER', 'root')
    cred = factories.credential(kind='ssh', user=admin_user, username=sudo_user, become_method="sudo", password=None,
                                become_password=None)
    return cred


@pytest.fixture(scope="function", params=['sudo', 'su', 'pbrun', 'pfexec', 'dzdo'])
def ssh_credential_multi_ask(request, admin_user, factories):
    """Create ssh credential with multiple 'ASK' passwords"""
    if request.param not in ('sudo', 'su', 'pbrun', 'pfexec', 'dzdo'):
        raise Exception("Unsupported parameter value: %s" % request.param)

    cred = factories.credential(description="machine credential with multi-ASK password - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, password='ASK', ssh_key_unlock='ASK',
                                ssh_key_data=config.credentials.ssh.encrypted.ssh_key_data,
                                become_method=request.param, become_password='ASK')
    return cred


@pytest.fixture(scope="function")
def team_ssh_credential(team_with_org_admin, factories):
    cred = factories.credential(description="machine credential for team:%s" % team_with_org_admin.name,
                                kind='ssh', team=team_with_org_admin, ssh_key_data=None, become_password=None)
    return cred


# SSH machine credentials with different types of ssh_key_data
# Passphrases for all encrypted keys is "fo0m4nchU"
@pytest.fixture
def unencrypted_rsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/unencrypted_rsa'), 'r').read()


@pytest.fixture(scope="function")
def unencrypted_rsa_ssh_credential(admin_user, unencrypted_rsa_ssh_key_data, factories):
    cred = factories.credential(name="unencrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=unencrypted_rsa_ssh_key_data,
                                password=None, become_password=None)
    return cred


@pytest.fixture
def encrypted_rsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/encrypted_rsa'), 'r').read()


@pytest.fixture
def encrypted_rsa_ssh_key_data_pkcs8():
    return open(os.path.join(fixtures_dir, 'static/encrypted_rsa_pkcs8'), 'r').read()


@pytest.fixture(scope="function")
def encrypted_rsa_ssh_credential(admin_user, encrypted_rsa_ssh_key_data, factories):
    cred = factories.credential(name="encrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_rsa_ssh_key_data,
                                ssh_key_unlock='ASK', password=None, become_password=None)
    return cred


@pytest.fixture(scope="function")
def encrypted_rsa_pkcs8_ssh_credential(admin_user, encrypted_rsa_ssh_key_data_pkcs8, factories):
    cred = factories.credential(name="encrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_rsa_ssh_key_data_pkcs8,
                                ssh_key_unlock='ASK', password=None, become_password=None)
    return cred


@pytest.fixture
def unencrypted_dsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/unencrypted_dsa'), 'r').read()


@pytest.fixture(scope="function")
def unencrypted_dsa_ssh_credential(admin_user, unencrypted_dsa_ssh_key_data, factories):
    cred = factories.credential(name="unencrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=unencrypted_dsa_ssh_key_data,
                                password=None, become_password=None)

    return cred


@pytest.fixture
def encrypted_dsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/encrypted_dsa'), 'r').read()


@pytest.fixture(scope="function")
def encrypted_dsa_ssh_credential(admin_user, encrypted_dsa_ssh_key_data, factories):
    cred = factories.credential(name="encrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_dsa_ssh_key_data,
                                ssh_key_unlock='ASK', password=None, become_password=None)
    return cred


@pytest.fixture
def unencrypted_ecdsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/unencrypted_ecdsa'), 'r').read()


@pytest.fixture(scope="function")
def unencrypted_ecdsa_ssh_credential(admin_user, unencrypted_ecdsa_ssh_key_data, factories):
    cred = factories.credential(name="unencrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=unencrypted_ecdsa_ssh_key_data,
                                password=None, become_password=None)
    return cred


@pytest.fixture
def encrypted_ecdsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/encrypted_ecdsa'), 'r').read()


@pytest.fixture
def encrypted_ecdsa_ssh_key_data_pkcs8():
    return open(os.path.join(fixtures_dir, 'static/encrypted_ecdsa_pkcs8'), 'r').read()


@pytest.fixture(scope="function")
def encrypted_ecdsa_ssh_credential(admin_user, encrypted_ecdsa_ssh_key_data, factories):
    cred = factories.credential(name="encrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_ecdsa_ssh_key_data,
                                ssh_key_unlock='ASK', password=None, become_password=None)

    return cred


@pytest.fixture(scope="function")
def encrypted_ecdsa_pkcs8_ssh_credential(admin_user, encrypted_ecdsa_ssh_key_data_pkcs8, factories):
    cred = factories.credential(name="encrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_ecdsa_ssh_key_data_pkcs8,
                                ssh_key_unlock='ASK', password=None, become_password=None)

    return cred


@pytest.fixture
def unencrypted_open_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/unencrypted_open_rsa'), 'r').read()


@pytest.fixture(scope="function")
def unencrypted_open_ssh_credential(admin_user, unencrypted_open_ssh_key_data, factories):
    cred = factories.credential(name="unencrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=unencrypted_open_ssh_key_data,
                                password=None, become_password=None)
    return cred


@pytest.fixture
def encrypted_open_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/encrypted_open_rsa'), 'r').read()


@pytest.fixture(scope="function")
def encrypted_open_ssh_credential(admin_user, encrypted_open_ssh_key_data, factories):
    cred = factories.credential(name="encrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_open_ssh_key_data,
                                ssh_key_unlock='ASK', password=None, become_password=None)
    return cred


# Convenience fixture that iterates through ssh credentials
ssh_credential_params = ['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open',
                         'encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open']


@pytest.fixture(
    scope="function",
    params=ssh_credential_params,
    ids=ssh_credential_params,
)
def ssh_credential_with_ssh_key_data(request, params=ssh_credential_params):
    return (request.param, request.getfixturevalue(request.param + '_ssh_credential'))


# Convenience fixture that iterates through unencrypted ssh credentials
unencrypted_ssh_credential_params = ['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open']


@pytest.fixture(
    scope="function",
    params=unencrypted_ssh_credential_params,
    ids=unencrypted_ssh_credential_params,
)
def unencrypted_ssh_credential_with_ssh_key_data(request):
    return (request.param, request.getfixturevalue(request.param + '_ssh_credential'))


# Convenience fixture that iterates through encrypted ssh credentials
encrypted_ssh_credential_params = [
    'encrypted_rsa',
    'encrypted_dsa',
    'encrypted_ecdsa',
    'encrypted_open',
    'encrypted_rsa_pkcs8',
    'encrypted_ecdsa_pkcs8'
]


@pytest.fixture(
    scope="function",
    params=encrypted_ssh_credential_params,
    ids=encrypted_ssh_credential_params,
)
def encrypted_ssh_credential_with_ssh_key_data(request, is_fips_enabled):

    if is_fips_enabled and 'pkcs8' not in request.param:
        pytest.skip('Cannot run on a FIPS enabled platform')

    return (request.param, request.getfixturevalue(request.param + '_ssh_credential'))


# Network credentials
@pytest.fixture
def network_credential_type(v2):
    return v2.credential_types.get(name__icontains='network', managed_by_tower=True).results.pop()


@pytest.fixture(scope="function")
def network_credential_with_basic_auth(admin_user, factories, network_credential_type):
    cred = factories.credential(name="network credentials-%s" % fauxfactory.gen_utf8(),
                                description="network credential - %s" % fauxfactory.gen_utf8(),
                                credential_type=network_credential_type, user=admin_user, ssh_key_data=None, authorize_password=None)
    return cred


@pytest.fixture(scope="function")
def network_credential_with_authorize(admin_user, factories, network_credential_type):
    cred = factories.credential(name="network credentials-%s" % fauxfactory.gen_utf8(),
                                description="network credential - %s" % fauxfactory.gen_utf8(),
                                credential_type=network_credential_type, user=admin_user, ssh_key_data=None)
    return cred


@pytest.fixture(scope="function")
def network_credential_with_ssh_key_data(admin_user, factories, network_credential_type):
    cred = factories.credential(name="network credentials-%s" % fauxfactory.gen_utf8(),
                                description="network credential - %s" % fauxfactory.gen_utf8(),
                                credential_type=network_credential_type, user=admin_user, password=None, authorize_password=None)
    return cred


# Convenience fixture that iterates through network credentials
@pytest.fixture(scope="function", params=['network_credential_with_basic_auth',
                                          'network_credential_with_authorize',
                                          'network_credential_with_ssh_key_data'])
def network_credential(request):
    return request.getfixturevalue(request.param)


# SCM credentials
@pytest.fixture(scope="function")
def unencrypted_scm_credential(admin_user, factories):
    cred = factories.credential(name="scm credentials-%s" % fauxfactory.gen_utf8(),
                                description="unencrypted scm credential - %s" % fauxfactory.gen_utf8(),
                                kind='scm', user=admin_user, password=None)
    return cred


@pytest.fixture(scope="function")
def encrypted_scm_credential(admin_user, factories):
    cred = factories.credential(name="scm credentials-%s" % fauxfactory.gen_utf8(),
                                description="encrypted scm credential - %s" % fauxfactory.gen_utf8(),
                                kind='scm', user=admin_user, ssh_key_data=config.credentials.scm.encrypted.ssh_key_data,
                                ssh_key_unlock=config.credentials.scm.encrypted.ssh_key_unlock, password=None)
    return cred


# Cloud credentials
@pytest.fixture(scope="class")
def aws_credential(admin_user, class_factories):
    cred = class_factories.credential(name="awx-credential-%s" % fauxfactory.gen_utf8(),
                                description="AWS credential %s" % fauxfactory.gen_utf8(),
                                kind='aws', user=admin_user)
    return cred


@pytest.fixture(scope="class")
def azure_credential(admin_user, class_factories):
    cred = class_factories.credential(name="azure-credential-%s" % fauxfactory.gen_utf8(),
                                description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                                kind='azure_rm', user=admin_user)
    return cred


@pytest.fixture(scope="class")
def gce_credential(admin_user, class_factories):
    cred = class_factories.credential(name="gce-credential-%s" % fauxfactory.gen_utf8(),
                                description="Google Compute Engine credential %s" % fauxfactory.gen_utf8(),
                                kind='gce', user=admin_user)
    return cred


@pytest.fixture(scope="class")
def vmware_credential(admin_user, class_factories):
    cred = class_factories.credential(name="vmware-credential-%s" % fauxfactory.gen_utf8(),
                                description="VMware vCenter credential %s" % fauxfactory.gen_utf8(),
                                kind='vmware', user=admin_user)
    return cred


@pytest.fixture(scope="class")
def openstack_v3_credential(admin_user, class_factories):
    cred = class_factories.credential(name="openstack-v3-credential-%s" % fauxfactory.gen_utf8(),
                                description="OpenStack credential %s" % fauxfactory.gen_utf8(),
                                kind='openstack', user=admin_user,
                                inputs=dict(host=config.credentials.cloud.openstack_v3.host,
                                domain=config.credentials.cloud.openstack_v3.domain,
                                password=config.credentials.cloud.openstack_v3.password,
                                username=config.credentials.cloud.openstack_v3.username,
                                project=config.credentials.cloud.openstack_v3.project,
                                ))
    return cred


@pytest.fixture(scope="function", params=['openstack_v3_credential'])
def openstack_credential(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def cloudforms_credential(admin_user, factories):
    cred = factories.credential(name="cloudforms-credentials-%s" % fauxfactory.gen_utf8(),
                                description="CloudForms credential - %s" % fauxfactory.gen_utf8(),
                                kind='cloudforms', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def satellite6_credential(admin_user, factories):
    cred = factories.credential(name="satellite6-credentials-%s" % fauxfactory.gen_utf8(),
                                description="Satellite6 credential - %s" % fauxfactory.gen_utf8(),
                                kind='satellite6', user=admin_user)
    return cred


# Convenience fixture that iterates through supported cloud_credential types
@pytest.fixture(scope="function", params=['aws', 'azure', 'gce', 'vmware', 'openstack_v3', 'cloudforms', 'satellite6'])
def cloud_credential(request):
    return request.getfixturevalue(request.param + '_credential')

# Github/ Gitlab credentials
@pytest.fixture(scope="class")
def github_credential(v2_class, class_factories):
    credential_type_github = v2_class.credential_types.get(namespace="github_token").results.pop().id
    cred = class_factories.credential(credential_type=credential_type_github)
    return cred


@pytest.fixture(scope="class")
def gitlab_credential(v2_class, class_factories):
    credential_type_gitlab = v2_class.credential_types.get(namespace="gitlab_token").results.pop().id
    cred = class_factories.credential(credential_type=credential_type_gitlab)
    return cred

# Kubernetes
#
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
    utils.poll_until(lambda: requests.get(vault_url).status_code == 200, timeout=120)

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
    sess.post('{}/v1/versioned/data/subfolder/example-user'.format(vault_url), json={
        "data": {
            "username": "sub-username"
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
