import pytest
import fauxfactory
import os
# from users import admin_user


fixtures_dir = os.path.dirname(__file__)


@pytest.fixture(scope="function")
def credential_kind_choices(request, authtoken, api_credentials_pg):
    '''Return ssh credential'''
    return dict(api_credentials_pg.options().json['actions']['POST']['kind']['choices'])


@pytest.fixture(scope="function")
def ssh_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential'''
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
def ssh_credential_ask(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential with 'ASK' password'''
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
    '''Create ssh credential with the following properties:
        * username: SUDO_USER
        * become_method: sudo
        * ssh_key_data: <str>
    '''
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
    '''Create ssh credential with multiple 'ASK' passwords'''
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
def team_ssh_credential(request, testsetup, authtoken, team_with_org_admin):
    '''Create team ssh credential'''
    payload = dict(name="credential-%s" % fauxfactory.gen_utf8(),
                   description="machine credential for team:%s" % team_with_org_admin.name,
                   kind='ssh',
                   team=team_with_org_admin.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)
    obj = team_with_org_admin.get_related('credentials').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def aws_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Amazon Cloud credential'''
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
    '''Create a randomly named Rackspace Cloud credential'''
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
def azure_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Azure Cloud credential'''
    payload = dict(name="azure-credential-%s" % fauxfactory.gen_utf8(),
                   description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                   kind='azure',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['azure']['username'],
                   ssh_key_data=testsetup.credentials['cloud']['azure']['ssh_key_data'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def gce_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Google Compute Engine credential'''
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
    '''Create a randomly named VMware vCenter credential'''
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
def openstack_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Openstack credential'''
    payload = dict(name="openstack-credential-%s" % fauxfactory.gen_utf8(),
                   description="Openstack credential %s" % fauxfactory.gen_utf8(),
                   kind='openstack',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['openstack']['host'],
                   username=testsetup.credentials['cloud']['openstack']['username'],
                   password=testsetup.credentials['cloud']['openstack']['password'],
                   project=testsetup.credentials['cloud']['openstack']['project'])
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


#
# Convenience fixture that iterates through supported cloud_credential types
#
@pytest.fixture(scope="function", params=['aws', 'rax', 'azure', 'gce', 'vmware', 'openstack'])
def cloud_credential(request):
    return request.getfuncargvalue(request.param + '_credential')


@pytest.fixture(scope="function")
def scm_credential_key_unlock_ASK(request, authtoken, api_credentials_pg, admin_user):
    '''Create scm credential with scm_key_unlock="ASK"'''
    payload = dict(name="credentials-%s" % fauxfactory.gen_utf8(),
                   description="SCM credential %s (scm_key_unlock:ASK)" % fauxfactory.gen_utf8(),
                   kind='scm',
                   username='git',
                   scm_key_unlock='ASK',
                   user=admin_user.id,)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def many_ssh_credentials(request, authtoken, testsetup, api_credentials_pg, admin_user):
    obj_list = list()
    for i in range(55):
        payload = dict(name="credential_%d_%s" % (i, fauxfactory.gen_utf8()),
                       description="machine credential - %d - %s" % (i, fauxfactory.gen_utf8()),
                       kind='ssh',
                       user=admin_user.id,
                       username=testsetup.credentials['ssh']['username'],
                       password=testsetup.credentials['ssh']['password'],)
        obj = api_credentials_pg.post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list


# The following ssh keys were generated by command line.
# Passphrases for all encrypted keys is "fo0m4nchU"

#
# Unencrypted RSA ssh key
#
@pytest.fixture(scope="function")
def unencrypted_rsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create rsa ssh_credential'''
    payload = dict(name="unencrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/unencrypted_rsa'), 'r').read())

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Encrypted RSA ssh key
#
@pytest.fixture(scope="function")
def encrypted_rsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create rsa ssh_credential'''
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


#
# Unencrypted DSA ssh key
#
@pytest.fixture(scope="function")
def unencrypted_dsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create dsa ssh_credential'''
    payload = dict(name="unencrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/unencrypted_dsa'), 'r').read())

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Encrypted DSA ssh key
#
@pytest.fixture(scope="function")
def encrypted_dsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create dsa ssh_credential'''
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


#
# Unencrypted ECDSA ssh key
#
@pytest.fixture(scope="function")
def unencrypted_ecdsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create ecdsa ssh_credential'''
    payload = dict(name="unencrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/unencrypted_ecdsa'), 'r').read())

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Encrypted ECDSA ssh key
#
@pytest.fixture(scope="function")
def encrypted_ecdsa_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create ecdsa ssh_credential'''
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


#
# Unencrypted open ssh key
#
@pytest.fixture(scope="function")
def unencrypted_open_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create open ssh_credential'''
    payload = dict(name="unencrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                   description="machine credential - %s" % fauxfactory.gen_utf8(),
                   kind='ssh',
                   user=admin_user.id,
                   username=fauxfactory.gen_alphanumeric(),
                   ssh_key_data=open(os.path.join(fixtures_dir, 'static/unencrypted_open_rsa'), 'r').read())

    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Encrypted open ssh key
#
@pytest.fixture(scope="function")
def encrypted_open_ssh_credential(request, authtoken, api_credentials_pg, admin_user):
    '''Create open ssh_credential'''
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
ssh_credential_with_ssh_key_data_params = ['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open',
                                           'encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open']


@pytest.fixture(
    scope="function",
    params=ssh_credential_with_ssh_key_data_params,
    ids=ssh_credential_with_ssh_key_data_params,
)
def ssh_credential_with_ssh_key_data(request):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))


#
# Convenience fixture that iterates through unencrypted ssh credentials
#
ssh_credential_with_ssh_key_data_params = ['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open']


@pytest.fixture(
    scope="function",
    params=ssh_credential_with_ssh_key_data_params,
    ids=ssh_credential_with_ssh_key_data_params,
)
@pytest.fixture(scope="function", params=['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open'])
def unencrypted_ssh_credential_with_ssh_key_data(request):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))


#
# Convenience fixture that iterates through encrypted ssh credentials
#
ssh_credential_with_ssh_key_data_params = ['encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open']


@pytest.fixture(
    scope="function",
    params=ssh_credential_with_ssh_key_data_params,
    ids=ssh_credential_with_ssh_key_data_params,
)
@pytest.fixture(scope="function", params=['encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open'])
def encrypted_ssh_credential_with_ssh_key_data(request):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))
