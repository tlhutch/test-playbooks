import pytest
import fauxfactory
# from users import admin_user


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
