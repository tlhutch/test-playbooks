import pytest
import common.utils
# from users import admin_user


@pytest.fixture(scope="function")
def credential_kind_choices(request, authtoken, api_credentials_pg):
    '''Return ssh credential'''
    return dict(api_credentials_pg.options().json['actions']['POST']['kind']['choices'])


@pytest.fixture(scope="function")
def ssh_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential'''
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="machine credential - %s" % common.utils.random_unicode(),
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
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="machine credential with ASK password - %s" % common.utils.random_unicode(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password='ASK',)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def ssh_credential_multi_ask(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential with multiple 'ASK' passwords'''
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="machine credential with mulit-ASK password - %s" % common.utils.random_unicode(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password='ASK',
                   ssh_key_data=testsetup.credentials['ssh']['encrypted']['ssh_key_data'],
                   ssh_key_unlock='ASK',
                   sudo_username=testsetup.credentials['ssh']['sudo_username'],
                   sudo_password='ASK',
                   vault_password='ASK',)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def aws_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Amazon Cloud credential'''
    payload = dict(name="awx-credential-%s" % common.utils.random_unicode(),
                   description="AWS credential %s" % common.utils.random_unicode(),
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
    payload = dict(name="rax-credential-%s" % common.utils.random_unicode(),
                   description="Rackspace credential %s" % common.utils.random_unicode(),
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
    payload = dict(name="azure-credential-%s" % common.utils.random_unicode(),
                   description="Microsoft Azure credential %s" % common.utils.random_unicode(),
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
    payload = dict(name="gce-credential-%s" % common.utils.random_unicode(),
                   description="Google Compute Engine credential %s" % common.utils.random_unicode(),
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
    payload = dict(name="vmware-credential-%s" % common.utils.random_unicode(),
                   description="VMware vCenter credential %s" % common.utils.random_unicode(),
                   kind='vmware',
                   user=admin_user.id,
                   host=testsetup.credentials['cloud']['vmware']['host'],
                   username=testsetup.credentials['cloud']['vmware']['username'],
                   password=testsetup.credentials['cloud']['vmware']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def scm_credential_key_unlock_ASK(request, authtoken, api_credentials_pg, admin_user):
    '''Create scm credential with scm_key_unlock="ASK"'''
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="SCM credential %s (scm_key_unlock:ASK)" % common.utils.random_unicode(),
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
        payload = dict(name="credential_%d_%s" % (i, common.utils.random_unicode()),
                       description="machine credential - %d - %s" % (i, common.utils.random_unicode()),
                       kind='ssh',
                       user=admin_user.id,
                       username=testsetup.credentials['ssh']['username'],
                       password=testsetup.credentials['ssh']['password'],)
        obj = api_credentials_pg.post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list
