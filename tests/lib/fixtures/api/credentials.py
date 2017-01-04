import pytest
import fauxfactory
import os
# from users import admin_user


fixtures_dir = os.path.dirname(__file__)


@pytest.fixture(scope="function")
def credential_kind_choices(request, authtoken, api_credentials_pg):
    """Return ssh credential"""
    return dict(api_credentials_pg.options().json['actions']['POST']['kind']['choices'])


#
# SSH machine credentials
#
@pytest.fixture(scope="function")
def ssh_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create ssh credential"""
    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)

    # TODO - support overriding the payload via a pytest marker
    fixture_args = getattr(request.function, 'ssh_credential', None)
    if fixture_args and 'kwargs' in fixture_args:
        payload.update(fixture_args.kwargs)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def another_ssh_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create another ssh credential"""
    payload = dict(name="another credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)

    # TODO - support overriding the payload via a pytest marker
    fixture_args = getattr(request.function, 'ssh_credential', None)
    if fixture_args and 'kwargs' in fixture_args:
        payload.update(fixture_args.kwargs)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def ssh_credential_ask(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create ssh credential with 'ASK' password"""
    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential with ASK password - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password='ASK',)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def ssh_credential_with_ssh_key_data_and_sudo(request, ansible_facts, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create ssh credential with the following properties:
    * username: SUDO_USER
    * become_method: sudo
    * ssh_key_data: <str>
    """
    SUDO_USER = ansible_facts.values()[0]['ansible_facts']['ansible_env']['SUDO_USER']

    payload = dict(name=fauxfactory.gen_utf8(),
                   description=fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=SUDO_USER,
                   become_method="sudo",
                   ssh_key_data=testsetup.credentials['ssh']['ssh_key_data'])

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function", params=['sudo', 'su', 'pbrun'])
def ssh_credential_multi_ask(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create ssh credential with multiple 'ASK' passwords"""
    if request.param not in ('sudo', 'su', 'pbrun'):
        raise Exception("Unsupported parameter value: %s" % request.param)

    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential with mulit-ASK password - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password='ASK',
                   ssh_key_data=testsetup.credentials['ssh']['encrypted']['ssh_key_data'],
                   ssh_key_unlock='ASK',
                   vault_password='ASK',
                   become_method=request.param,
                   become_username=testsetup.credentials['ssh']['become_username'],
                   become_password='ASK')
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def team_ssh_credential(request, authtoken, team_with_org_admin, testsetup):
    """Create team ssh credential"""
    payload = dict(name="credential-%s" % fauxfactory.gen_utf8(),
                   description="machine credential for team:%s" % team_with_org_admin.name,
                   kind='ssh',
                   team=team_with_org_admin.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)
    obj = team_with_org_admin.get_related('credentials').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# SSH machine credentials with different types of ssh_key_data
# Passphrases for all encrypted keys is "fo0m4nchU"
#
@pytest.fixture(scope="function")
def unencrypted_rsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    """Create rsa ssh_credential"""
    payload = dict(name="unencrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/unencrypted_rsa'), 'r').read())

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def encrypted_rsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    """Create rsa ssh_credential"""
    payload = dict(name="encrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/encrypted_rsa'), 'r').read(),
                   ssh_key_unlock='ASK')

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def unencrypted_dsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    """Create dsa ssh_credential"""
    payload = dict(name="unencrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/unencrypted_dsa'), 'r').read())

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def encrypted_dsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    """Create dsa ssh_credential"""
    payload = dict(name="encrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/encrypted_dsa'), 'r').read(),
                   ssh_key_unlock='ASK')

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def unencrypted_ecdsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    """Create ecdsa ssh_credential"""
    payload = dict(name="unencrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/unencrypted_ecdsa'), 'r').read())

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def encrypted_ecdsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    """Create ecdsa ssh_credential"""
    payload = dict(name="encrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/encrypted_ecdsa'), 'r').read(),
                   ssh_key_unlock='ASK')

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def unencrypted_open_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    """Create open ssh_credential"""
    payload = dict(name="unencrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/unencrypted_open_rsa'), 'r').read())

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def encrypted_open_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    """Create open ssh_credential"""
    payload = dict(name="encrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/encrypted_open_rsa'), 'r').read(),
                   ssh_key_unlock='ASK')

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Convenience fixture that iterates through ssh credentials
#
ssh_credential_params = ['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open',
                         'encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open']


@pytest.fixture(
    scope="function",
    params=ssh_credential_params,
    ids=ssh_credential_params,
)
def ssh_credential_with_ssh_key_data(request, params=ssh_credential_params):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))


#
# Convenience fixture that iterates through unencrypted ssh credentials
#
unencrypted_ssh_credential_params = ['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open']


@pytest.fixture(
    scope="function",
    params=unencrypted_ssh_credential_params,
    ids=unencrypted_ssh_credential_params,
)
@pytest.fixture(scope="function", params=unencrypted_ssh_credential_params)
def unencrypted_ssh_credential_with_ssh_key_data(request):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))


#
# Convenience fixture that iterates through encrypted ssh credentials
#
encrypted_ssh_credential_params = ['encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open']


@pytest.fixture(
    scope="function",
    params=encrypted_ssh_credential_params,
    ids=encrypted_ssh_credential_params,
)
@pytest.fixture(scope="function", params=encrypted_ssh_credential_params)
def encrypted_ssh_credential_with_ssh_key_data(request):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))


#
# Network credentials
#
@pytest.fixture(scope="function")
def network_credential_with_basic_auth(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create network credential"""
    payload = dict(name="network credentials-%s" % fauxfactory.gen_utf8(),
                   description="network credential - %s" % fauxfactory.gen_utf8(),
                   kind='net',
                   user=admin_user.id,
                   username=testsetup.credentials['network']['username'],
                   password=testsetup.credentials['network']['password'])

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def network_credential_with_authorize(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create network credential"""
    payload = dict(name="network credentials-%s" % fauxfactory.gen_utf8(),
                   description="network credential - %s" % fauxfactory.gen_utf8(),
                   kind='net',
                   user=admin_user.id,
                   username=testsetup.credentials['network']['username'],
                   password=testsetup.credentials['network']['password'],
                   authorize=True,
                   authorize_password=testsetup.credentials['network']['authorize'])

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def network_credential_with_ssh_key_data(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create network credential"""
    payload = dict(name="network credentials-%s" % fauxfactory.gen_utf8(),
                   description="network credential - %s" % fauxfactory.gen_utf8(),
                   kind='net',
                   user=admin_user.id,
                   username=testsetup.credentials['network']['username'],
                   ssh_key_data=testsetup.credentials['network']['ssh_key_data'])

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Convenience fixture that iterates through network credentials
#
@pytest.fixture(scope="function", params=['network_credential_with_basic_auth',
                                          'network_credential_with_authorize',
                                          'network_credential_with_ssh_key_data'])
def network_credential(request):
    return request.getfuncargvalue(request.param)


#
# SCM credentials
#
@pytest.fixture(scope="function")
def unencrypted_scm_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create an unencrypted scm credential"""
    payload = dict(name="scm credentials-%s" % fauxfactory.gen_utf8(),
                   description="unencrypted scm credential - %s" % fauxfactory.gen_utf8(),
                   kind='scm',
                   user=admin_user.id,
                   ssh_key_data=testsetup.credentials['scm']['ssh_key_data'],
                   ssh_key_unlock=testsetup.credentials['scm']['ssh_key_unlock'],)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def encrypted_scm_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create an encrypted scm credential"""
    payload = dict(name="scm credentials-%s" % fauxfactory.gen_utf8(),
                   description="encrypted scm credential - %s" % fauxfactory.gen_utf8(),
                   kind='scm',
                   user=admin_user.id,
                   ssh_key_data=testsetup.credentials['scm']['encrypted']['ssh_key_data'],
                   ssh_key_unlock=testsetup.credentials['scm']['encrypted']['ssh_key_unlock'],)

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def scm_credential_key_unlock_ASK(request, authtoken, api_credentials_pg, admin_user):
    """Create scm credential with scm_key_unlock='ASK'"""
    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="SCM credential %s (scm_key_unlock:ASK)" % fauxfactory.gen_utf8(),
                   kind='scm',
                   username='git',
                   scm_key_unlock='ASK',
                   user=admin_user.id,)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


#
# Cloud credentials
#
@pytest.fixture(scope="function")
def aws_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named Amazon cloud credential"""
    payload = dict(name="awx-credential-%s" % fauxfactory.gen_utf8(),
                   description="AWS credential %s" % fauxfactory.gen_utf8(),
                   kind='aws',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['aws']['username'],
                   password=testsetup.credentials['cloud']['aws']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def rax_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named Rackspace cloud credential"""
    payload = dict(name="rax-credential-%s" % fauxfactory.gen_utf8(),
                   description="Rackspace credential %s" % fauxfactory.gen_utf8(),
                   kind='rax',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['rax']['username'],
                   password=testsetup.credentials['cloud']['rax']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def azure_classic_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named Azure classic cloud credential"""
    payload = dict(name="azure-classic-credential-%s" % fauxfactory.gen_utf8(),
                   description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                   kind='azure',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['azure_classic']['username'],
                   ssh_key_data=testsetup.credentials['cloud']['azure_classic']['ssh_key_data'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def azure_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named Azure cloud credential"""
    payload = dict(name="azure-credential-%s" % fauxfactory.gen_utf8(),
                   description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                   kind='azure_rm',
                   user=admin_user.id,
                   subscription=testsetup.credentials['cloud']['azure']['subscription_id'],
                   client=testsetup.credentials['cloud']['azure']['client_id'],
                   secret=testsetup.credentials['cloud']['azure']['secret'],
                   tenant=testsetup.credentials['cloud']['azure']['tenant'])
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def azure_ad_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named Azure active directory cloud credential"""
    payload = dict(name="azure-ad-credential-%s" % fauxfactory.gen_utf8(),
                   description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                   kind='azure_rm',
                   user=admin_user.id,
                   subscription=testsetup.credentials['cloud']['azure_ad']['subscription_id'],
                   username=testsetup.credentials['cloud']['azure_ad']['ad_user'],
                   password=testsetup.credentials['cloud']['azure_ad']['password'])
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def gce_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named Google Compute Engine cloud credential"""
    payload = dict(name="gce-credential-%s" % fauxfactory.gen_utf8(),
                   description="Google Compute Engine credential %s" % fauxfactory.gen_utf8(),
                   kind='gce',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['gce']['username'],
                   project=testsetup.credentials['cloud']['gce']['project'],
                   ssh_key_data=testsetup.credentials['cloud']['gce']['ssh_key_data'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def vmware_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named VMware vCenter cloud credential"""
    payload = dict(name="vmware-credential-%s" % fauxfactory.gen_utf8(),
                   description="VMware vCenter credential %s" % fauxfactory.gen_utf8(),
                   kind='vmware',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['vmware']['host'],
                   username=testsetup.credentials['cloud']['vmware']['username'],
                   password=testsetup.credentials['cloud']['vmware']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def openstack_v2_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named OpenStack_v2 cloud credential"""
    payload = dict(name="openstack-v2-credential-%s" % fauxfactory.gen_utf8(),
                   description="OpenStack credential %s" % fauxfactory.gen_utf8(),
                   kind='openstack',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['openstack_v2']['host'],
                   username=testsetup.credentials['cloud']['openstack_v2']['username'],
                   password=testsetup.credentials['cloud']['openstack_v2']['password'],
                   project=testsetup.credentials['cloud']['openstack_v2']['project'])
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def openstack_v3_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create a randomly named OpenStack_v3 cloud credential"""
    payload = dict(name="openstack-v3-credential-%s" % fauxfactory.gen_utf8(),
                   description="OpenStack credential %s" % fauxfactory.gen_utf8(),
                   kind='openstack',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['openstack_v3']['host'],
                   username=testsetup.credentials['cloud']['openstack_v3']['username'],
                   password=testsetup.credentials['cloud']['openstack_v3']['password'],
                   project=testsetup.credentials['cloud']['openstack_v3']['project'],
                   domain=testsetup.credentials['cloud']['openstack_v3']['domain'])
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


#
# Convenience fixture that iterates through OpenStack credentials
#
@pytest.fixture(scope="function", params=['openstack_v2', 'openstack_v3'])
def openstack_credential(request):
    return request.getfuncargvalue(request.param + '_credential')


@pytest.fixture(scope="function")
def cloudforms_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create CloudForms credential"""
    payload = dict(name="cloudforms-credentials-%s" % fauxfactory.gen_utf8(),
                   description="CloudForms credential - %s" % fauxfactory.gen_utf8(),
                   kind='cloudforms',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['cloudforms']['host'],
                   username=testsetup.credentials['cloud']['cloudforms']['username'],
                   password=testsetup.credentials['cloud']['cloudforms']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def satellite6_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    """Create Satellite6 credential"""
    payload = dict(name="satellite6-credentials-%s" % fauxfactory.gen_utf8(),
                   description="Satellite6 credential - %s" % fauxfactory.gen_utf8(),
                   kind='satellite6',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['satellite6']['host'],
                   username=testsetup.credentials['cloud']['satellite6']['username'],
                   password=testsetup.credentials['cloud']['satellite6']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Convenience fixture that iterates through supported cloud_credential types
#
@pytest.fixture(scope="function", params=['aws', 'rax', 'azure_classic', 'azure', 'azure_ad', 'gce', 'vmware', 'openstack_v2',
                                          'openstack_v3', 'cloudforms', 'satellite6'])
def cloud_credential(request, ansible_os_family, ansible_distribution_major_version):
    if (ansible_os_family == 'RedHat' and ansible_distribution_major_version == '6' and request.param in ['azure', 'azure_ad']):
        pytest.skip("Inventory import %s not unsupported on EL6 platforms." % request.param)
    return request.getfuncargvalue(request.param + '_credential')
