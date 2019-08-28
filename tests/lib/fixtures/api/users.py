from awxkit.config import config
import awxkit.exceptions
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
    return request.getfixturevalue(request.param)


@pytest.fixture
def system_users(superuser, system_auditor):
    return (superuser, system_auditor)


@pytest.fixture(scope="function", params=('superuser', 'system_auditor'))
def system_user(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def non_superusers(org_admin, org_user, anonymous_user, system_auditor):
    """Return a list of non-superusers"""
    return (org_admin, org_user, anonymous_user, system_auditor)


@pytest.fixture(scope="function", params=('org_admin', 'org_user', 'anonymous_user', 'system_auditor'))
def non_superuser(request):
    """Return the fixture for the specified request.param"""
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def org_users(org_admin, org_user):
    """Return a list of organization users."""
    return (org_admin, org_user)


@pytest.fixture(scope="function", params=('org_admin', 'org_user'))
def organization_user(request):
    return request.getfixturevalue(request.param)


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
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def unprivileged_users(org_user, anonymous_user):
    """Return a list of unprivileged_users"""
    return (org_user, anonymous_user)


@pytest.fixture(scope="function", params=('org_user', 'anonymous_user'))
def unprivileged_user(request):
    """Return the fixture for the specified request.param"""
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def clean_user_orgs_and_teams(request, user=None):
    def func(user):
        def teardown():
            [o.delete() for o in user.related.organizations.get().results
                if o.name != 'Default']
            [t.delete() for t in user.related.teams.get().results]
            user.delete()
        request.addfinalizer(teardown)
    return func


@pytest.fixture(params=[
        'sysadmin',
        'org_admin',
        'wf_admin',
        'org_wf_admin',
        'org_approve',
        'wf_approve',
        'org_executor',
        'wf_executor',
        'org_read',
        'wf_read',
        'system_auditor',
        'user_in_org',
        'random_user'
    ])
def user_with_role_and_workflow_with_approval_node(request, factories):
    role = request.param
    fixture_args = request.node.get_closest_marker('fixture_args')
    if fixture_args and 'roles' in fixture_args.kwargs:
        only_create = fixture_args.kwargs['roles']
        if role not in only_create:
            pytest.skip()

    org = factories.organization()
    user = factories.user(organization=org)
    wfjt = factories.workflow_job_template(organization=org)
    assert org.id == user.related.organizations.get().results.pop().id
    if role == 'wf_executor':
        wfjt.set_object_roles(user, 'execute')
    if role == 'wf_read':
        wfjt.set_object_roles(user, 'read')
    if role == 'wf_approve':
        wfjt.set_object_roles(user, 'approve')
    if role == 'wf_admin':
        wfjt.set_object_roles(user, 'admin')
    if role == 'org_executor':
        org.set_object_roles(user, 'execute')
    if role == 'org_read':
        org.set_object_roles(user, 'read')
    if role == 'org_approve':
        org.set_object_roles(user, 'approve')
    if role == 'org_wf_admin':
        org.set_object_roles(user, 'workflow admin')
    if role == 'system_auditor':
        user.is_system_auditor = True
    if role == 'sysadmin':
        user.is_superuser = True
    if role == 'org_admin':
        org.set_object_roles(user, 'admin')
    elif role == 'user_in_org':
        # no further changes needed
        pass
    elif role == 'random_user':
        with pytest.raises(awxkit.exceptions.NoContent):
            org.related.users.post(dict(id=user.id, disassociate=True))
        random_org = factories.organization()
        with pytest.raises(awxkit.exceptions.NoContent):
            random_org.related.users.post(dict(id=user.id, associate=True))
    approval_node = factories.workflow_job_template_node(
        workflow_job_template=wfjt,
        unified_job_template=None
    ).make_approval_node()
    return user, wfjt, role, approval_node
