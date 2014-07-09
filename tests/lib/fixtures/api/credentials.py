import pytest
import common.utils
# from users import admin_user


@pytest.fixture(scope="class")
def ssh_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential'''
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="machine credential - %s" % common.utils.random_unicode(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="class")
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


@pytest.fixture(scope="class")
def ssh_credential_multi_ask(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create ssh credential with 'ASK' password'''
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="machine credential with mulit-ASK password - %s" % common.utils.random_unicode(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password='ASK',
                   ssh_key_unlock='ASK',
                   sudo_username=testsetup.credentials['ssh']['sudo_username'],
                   sudo_password='ASK',)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="class")
def aws_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Amazon Cloud credential'''
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="AWS credential %s" % common.utils.random_unicode(),
                   kind='aws',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['aws']['username'],
                   password=testsetup.credentials['cloud']['aws']['password'],)
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="class")
def rax_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    '''Create a randomly named Rackspace Cloud credential'''
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="Rackspace credential %s" % common.utils.random_unicode(),
                   kind='rax',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['rax']['username'],
                   password=testsetup.credentials['cloud']['rax']['password'],)
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
