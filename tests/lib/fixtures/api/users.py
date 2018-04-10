from towerkit.config import config
import fauxfactory
import pytest


@pytest.fixture(scope="class")
def admin_user(authtoken, api_users_pg, user_password):
    user = api_users_pg.get(username__iexact='admin').results.pop()
    user.password = user_password
    return user


@pytest.fixture(scope="session")
def user_password():
    return config.credentials.default.password


@pytest.fixture(scope="function")
def org_admin(organization, factories):
    user = factories.user(username="org_admin_%s" % fauxfactory.gen_alphanumeric(),
                          first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                          last_name="Admin (%s)" % fauxfactory.gen_utf8(),
                          organization=organization)
    organization.add_admin(user)
    return user


@pytest.fixture(scope="function")
def another_org_admin(another_organization, factories):
    user = factories.user(username="org_admin_%s" % fauxfactory.gen_alphanumeric(),
                          first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                          last_name="Admin (%s)" % fauxfactory.gen_utf8(),
                          organization=another_organization)
    another_organization.add_admin(user)
    return user


@pytest.fixture(scope="function")
def org_user(organization, factories):
    user = factories.user(username="org_user_%s" % fauxfactory.gen_alphanumeric(),
                          first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                          last_name="User (%s)" % fauxfactory.gen_utf8(),
                          organization=organization)
    return user


@pytest.fixture(scope="function")
def another_org_user(another_organization, factories):
    user = factories.user(username="org_user_%s" % fauxfactory.gen_alphanumeric(),
                          first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                          last_name="User (%s)" % fauxfactory.gen_utf8(),
                          organization=another_organization)
    return user


@pytest.fixture(scope="function")
def anonymous_user(authtoken, factories):
    user = factories.user(username="anonymous_%s" % fauxfactory.gen_alphanumeric(),
                          first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                          last_name="User (%s)" % fauxfactory.gen_utf8())
    return user


@pytest.fixture(scope="function")
def superuser(authtoken, factories):
    user = factories.user(username="superuser_%s" % fauxfactory.gen_alphanumeric(),
                          first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                          last_name="Superuser (%s)" % fauxfactory.gen_utf8(),
                          is_superuser=True)
    return user


@pytest.fixture
def system_auditor(authtoken, factories):
    user = factories.user(username="system_auditor_%s" % fauxfactory.gen_alphanumeric(),
                          first_name="Joe (%s)" % fauxfactory.gen_utf8(),
                          last_name="System Auditor (%s)" % fauxfactory.gen_utf8(),
                          is_system_auditor=True)
    return user


@pytest.fixture(scope="function")
def all_users(superuser, org_admin, org_user, anonymous_user, system_auditor):
    """Return a list of user types"""
    return (superuser, org_admin, org_user, anonymous_user, system_auditor)


@pytest.fixture(scope="function", params=('superuser', 'org_admin', 'org_user', 'anonymous_user', 'system_auditor'))
def all_user(request):
    """Return the fixture for the specified request.param"""
    return request.getfuncargvalue(request.param)


@pytest.fixture
def system_users(superuser, system_auditor):
    return (superuser, system_auditor)


@pytest.fixture(scope="function")
def non_superusers(org_admin, org_user, anonymous_user, system_auditor):
    """Return a list of non-superusers"""
    return (org_admin, org_user, anonymous_user, system_auditor)


@pytest.fixture(scope="function", params=('org_admin', 'org_user', 'anonymous_user', 'system_auditor'))
def non_superuser(request):
    """Return the fixture for the specified request.param"""
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def org_users(org_admin, org_user):
    """Return a list of organization users."""
    return (org_admin, org_user)


@pytest.fixture(scope="function")
def non_org_users(anonymous_user, another_org_admin, another_org_user):
    """Return a list of organization users outside of 'Default' organization."""
    return (anonymous_user, another_org_admin, another_org_user)


@pytest.fixture(scope="function")
def privileged_users(superuser, org_admin):
    """Return a list of privileged_users"""
    return (superuser, org_admin)


@pytest.fixture(scope="function", params=('superuser', 'org_admin'))
def privileged_user(request):
    """Return the fixture for the specified request.param"""
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def unprivileged_users(org_user, anonymous_user):
    """Return a list of unprivileged_users"""
    return (org_user, anonymous_user)


@pytest.fixture(scope="function", params=('org_user', 'anonymous_user'))
def unprivileged_user(request):
    """Return the fixture for the specified request.param"""
    return request.getfuncargvalue(request.param)
