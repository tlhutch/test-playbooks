import pytest
import common.utils


@pytest.fixture(scope="class")
def admin_user(request, authtoken, api_users_pg):
    return api_users_pg.get(username__iexact='admin').results[0]


@pytest.fixture(scope="function")
def user_password(request):
    return "password"
    return common.utils.random_unicode()


@pytest.fixture(scope="function")
def org_admin(request, authtoken, organization, user_password):
    payload = dict(username="org_admin_%s" % common.utils.random_ascii(),
                   first_name="Joe (%s)" % common.utils.random_unicode(),
                   last_name="Admin (%s)" % common.utils.random_unicode(),
                   email="org_admin_%s@example.com" % common.utils.random_ascii(),
                   password=user_password,
                   organization=organization.id,)
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
