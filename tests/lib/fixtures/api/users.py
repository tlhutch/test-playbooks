import pytest
import fauxfactory
import contextlib
import qe.exceptions


@pytest.fixture(scope="class")
def admin_user(request, authtoken, api_users_pg):
    return api_users_pg.get(username__iexact='admin').results[0]


@pytest.fixture(scope="function")
def user_password(request):
    return "fo0m4nchU"


@pytest.fixture(scope="function")
def org_admin(request, authtoken, organization, user_password):
    payload = dict(username="org_admin_%s" % fauxfactory.gen_alphanumeric(),
                   first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                   last_name="Admin (%s)" % fauxfactory.gen_utf8(),
                   email=fauxfactory.gen_email(),
                   password=user_password,
                   organization=organization.id,
                   is_superuser=False)
    obj = organization.get_related('admins').post(payload)
    request.addfinalizer(obj.silent_delete)
    # Add as organization user
    with pytest.raises(qe.exceptions.NoContent_Exception):
        organization.get_related('users').post(dict(id=obj.id))
    return obj


@pytest.fixture(scope="function")
def another_org_admin(request, authtoken, another_organization, user_password):
    payload = dict(username="org_admin_%s" % fauxfactory.gen_alphanumeric(),
                   first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                   last_name="Admin (%s)" % fauxfactory.gen_utf8(),
                   email=fauxfactory.gen_email(),
                   password=user_password,
                   organization=another_organization.id,)
    obj = another_organization.get_related('admins').post(payload)
    request.addfinalizer(obj.delete)
    # Add as organization user
    with pytest.raises(qe.exceptions.NoContent_Exception):
        another_organization.get_related('users').post(dict(id=obj.id))
    return obj


@pytest.fixture(scope="function")
def org_user(request, authtoken, organization, user_password):
    payload = dict(username="org_user_%s" % fauxfactory.gen_alphanumeric(),
                   first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                   last_name="User (%s)" % fauxfactory.gen_utf8(),
                   email=fauxfactory.gen_email(),
                   password=user_password,
                   organization=organization.id,)
    obj = organization.get_related('users').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def another_org_user(request, authtoken, another_organization, user_password):
    payload = dict(username="org_user_%s" % fauxfactory.gen_alphanumeric(),
                   first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                   last_name="User (%s)" % fauxfactory.gen_utf8(),
                   email=fauxfactory.gen_email(),
                   password=user_password,
                   organization=another_organization.id,)
    obj = another_organization.get_related('users').post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def anonymous_user(request, authtoken, api_users_pg, user_password):
    payload = dict(username="anonymous_%s" % fauxfactory.gen_alphanumeric(),
                   first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                   last_name="User (%s)" % fauxfactory.gen_utf8(),
                   email=fauxfactory.gen_email(),
                   password=user_password,)
    obj = api_users_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def superuser(request, authtoken, api_users_pg, user_password):
    payload = dict(username="superuser_%s" % fauxfactory.gen_alphanumeric(),
                   first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                   last_name="Superuser (%s)" % fauxfactory.gen_utf8(),
                   email=fauxfactory.gen_email(),
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
def org_users(request, org_admin, org_user):
    '''
    Return a list of organization users.
    '''
    return (org_admin, org_user)


@pytest.fixture(scope="function")
def privileged_users(request, superuser, org_admin):
    '''
    Return a list of privileged_users
    '''
    return (superuser, org_admin)


@pytest.fixture(scope="function", params=('superuser', 'org_admin'))
def privileged_user(request):
    '''
    Return the fixture for the specified request.param
    '''
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def unprivileged_users(request, org_user, anonymous_user):
    '''
    Return a list of unprivileged_users
    '''
    return (org_user, anonymous_user)


@pytest.fixture(scope="function", params=('org_user', 'anonymous_user'))
def unprivileged_user(request):
    '''
    Return the fixture for the specified request.param
    '''
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def current_user(request, testsetup):
    '''
    Return a context manager to allow performing operations as an alternate user
    '''
    @contextlib.contextmanager
    def ctx(username=None, password=None):
        try:
            previous_auth = testsetup.api.session.auth
            testsetup.api.login(username, password)
            yield
        finally:
            testsetup.api.session.auth = previous_auth
    return ctx
