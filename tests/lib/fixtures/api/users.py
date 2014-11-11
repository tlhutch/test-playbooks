import pytest
import common.utils


@pytest.fixture(scope="class")
def admin_user(request, authtoken, api_users_pg):
    return api_users_pg.get(username__iexact='admin').results[0]


@pytest.fixture(scope="function")
def user_password(request):
    return "password"


@pytest.fixture(scope="function")
def org_admin(request, authtoken, organization, user_password):
    payload = dict(username="org_admin_%s" % common.utils.random_ascii(),
                   first_name="Joe (%s)" % common.utils.random_unicode(),
                   last_name="Admin (%s)" % common.utils.random_unicode(),
                   email="org_admin_%s@example.com" % common.utils.random_ascii(),
                   password=user_password,
                   organization=organization.id,
                   is_superuser=False)
    obj = organization.get_related('admins').post(payload)
    request.addfinalizer(obj.delete)
    # Add as organization user
    with pytest.raises(common.exceptions.NoContent_Exception):
        organization.get_related('users').post(dict(id=obj.id))
    return obj


@pytest.fixture(scope="function")
def another_org_admin(request, authtoken, another_organization, user_password):
    payload = dict(username="org_admin_%s" % common.utils.random_ascii(),
                   first_name="Joe (%s)" % common.utils.random_unicode(),
                   last_name="Admin (%s)" % common.utils.random_unicode(),
                   email="org_admin_%s@example.com" % common.utils.random_ascii(),
                   password=user_password,
                   organization=another_organization.id,)
    obj = another_organization.get_related('admins').post(payload)
    request.addfinalizer(obj.delete)
    # Add as organization user
    with pytest.raises(common.exceptions.NoContent_Exception):
        another_organization.get_related('users').post(dict(id=obj.id))
    return obj


@pytest.fixture(scope="function")
def org_user(request, authtoken, organization, user_password):
    payload = dict(username="org_user_%s" % common.utils.random_ascii(),
                   first_name="Joe (%s)" % common.utils.random_unicode(),
                   last_name="User (%s)" % common.utils.random_unicode(),
                   email="org_user_%s@example.com" % common.utils.random_ascii(),
                   password=user_password,
                   organization=organization.id,)
    obj = organization.get_related('users').post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def another_org_user(request, authtoken, another_organization, user_password):
    payload = dict(username="org_user_%s" % common.utils.random_ascii(),
                   first_name="Joe (%s)" % common.utils.random_unicode(),
                   last_name="User (%s)" % common.utils.random_unicode(),
                   email="org_user_%s@example.com" % common.utils.random_ascii(),
                   password=user_password,
                   organization=another_organization.id,)
    obj = another_organization.get_related('users').post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def anonymous_user(request, authtoken, api_users_pg, user_password):
    payload = dict(username="anonymous_%s" % common.utils.random_ascii(),
                   first_name="Joe (%s)" % common.utils.random_unicode(),
                   last_name="User (%s)" % common.utils.random_unicode(),
                   email="anonymous_user_%s@example.com" % common.utils.random_ascii(),
                   password=user_password,)
    obj = api_users_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def superuser(request, authtoken, api_users_pg, user_password):
    payload = dict(username="superuser_%s" % common.utils.random_ascii(),
                   first_name="Joe (%s)" % common.utils.random_unicode(),
                   last_name="Superuser (%s)" % common.utils.random_unicode(),
                   email="super_user_%s@example.com" % common.utils.random_ascii(),
                   password=user_password,
                   is_superuser=True)
    obj = api_users_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def all_users(request, superuser, org_admin, org_user, anonymous_user):
    '''
    Return a list of user types
    '''
    return (superuser, org_admin, org_user, anonymous_user)


@pytest.fixture(scope="function", params=('superuser', 'org_admin', 'org_user', 'anonymous_user'))
def all_user(request):
    '''
    Return the fixture for the specified request.param
    '''
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def non_superusers(request, org_admin, org_user, anonymous_user):
    '''
    Return a list of non-superusers
    '''
    return (org_admin, org_user, anonymous_user)


@pytest.fixture(scope="function", params=('org_admin', 'org_user', 'anonymous_user'))
def non_superuser(request):
    '''
    Return the fixture for the specified request.param
    '''
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def many_users(request, authtoken, api_users_pg, user_password):
    obj_list = list()
    for i in range(55):
        payload = dict(username="anonymous_%d_%s" % (i, common.utils.random_ascii()),
                       first_name="Joe (%s)" % common.utils.random_unicode(),
                       last_name="User (%s)" % common.utils.random_unicode(),
                       email="anonymous_%d_%s@example.com" % (i, common.utils.random_ascii()),
                       password=user_password,)
        obj = api_users_pg.post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list
