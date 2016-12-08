from contextlib import contextmanager
import httplib
import logging
import os

from towerkit.api.pages.users import User_Page
from towerkit.api.pages.teams import Team_Page
from towerkit.yaml_file import load_file
import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


# load expected values for summary_fields user_capabilities
user_capabilities = load_file(os.path.join(os.path.dirname(__file__), 'user_capabilities.yml'))

pytestmark = [
    pytest.mark.nondestructive,
    pytest.mark.skip_selenium,
    pytest.mark.rbac,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license'
    ),
]


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def auth_user(testsetup, authtoken, api_authtoken_url):
    """Inject a context manager for user authtoken switching on api models.
    The context manager is a wrapped function which takes a user api model
    and optional password.
    """
    @contextmanager
    def _auth_user(user, password='fo0m4nchU'):
        """Switch authorization context to that of a user corresponding to
        the api model of a user details endpoint.

        :param user: The api page model for a user
        :param password: (optional[str]): The password of the user

        Usage::
            >>> # patch a job template as a user with insufficient permissions
            >>> foo_job_template = factories.job_template(name='foo')
            >>> bar_inventory = factories.inventory(name='bar')
            >>> test_user = factories.user(username='phil')
            >>> with auth_user(test_user):
            >>>     foo_job_template.patch(inventory=bar_inventory.id)
            *** Forbidden
        """
        prev_auth = testsetup.api.session.auth
        data = {'username': user.username, 'password': password}
        response = testsetup.api.post(api_authtoken_url, data)
        testsetup.api.login(token=response.json()['token'])
        yield
        testsetup.api.session.auth = prev_auth
    return _auth_user


@pytest.fixture
def set_test_roles(factories):
    """Helper fixture used in creating the roles used in our RBAC tests.
    """
    def func(user_pg, tower_object, agent, role):
        """
        :param user_pg: The api page model for a user
        :param tower_object: Test Tower resource (a job template for example)
        :param agent: Either "user" or "team"; used for test parametrization
        :param role: Test role to give to our user_pg

        Note: the organization of our team matters when we're testing
        credentials.
        """
        if agent == "user":
            set_roles(user_pg, tower_object, [role])
        elif agent == "team":
            # create our team in our user organization if applicable
            organizations_pg = user_pg.get_related("organizations")
            if organizations_pg.results:
                team_pg = factories.team(organization=organizations_pg.results[0])
            else:
                team_pg = factories.team()
            set_roles(user_pg, team_pg, ['member'])
            set_roles(team_pg, tower_object, [role])
        else:
            raise ValueError("Unhandled 'agent' value.")
    return func


@pytest.fixture(scope="function", params=['organization', 'job_template', 'custom_inventory_source', 'project'])
def notifiable_resource(request):
    '''Iterates through the Tower objects that support notifications.'''
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function", params=['organization', 'job_template', 'custom_inventory_source', 'project'])
def resource_with_notification(request, email_notification_template):
    '''Tower resource with an associated email notification template.'''
    resource = request.getfuncargvalue(request.param)

    # associate our email NT with all notification template endpoints
    payload = dict(id=email_notification_template.id)
    endpoints = ['notification_templates_any', 'notification_templates_success', 'notification_templates_error']
    for endpoint in endpoints:
        with pytest.raises(towerkit.execeptions.NoContent):
            resource.get_related(endpoint).post(payload)
    return resource


# -----------------------------------------------------------------------------
# RBAC Utilities
# -----------------------------------------------------------------------------

def get_role(model, role_name):
    """Lookup and return a return a role page model by its role name.

    :param model: A resource api page model with related roles endpoint
    :role_name: The name of the role (case insensitive)

    Usage::
        >>> # get the description of the Use role for an inventory
        >>> bar_inventory = factories.inventory()
        >>> role_page = get_role(bar_inventory, 'Use')
        >>> role_page.description
        u'Can use the inventory in a job template'
    """
    search_name = role_name.lower()
    for role in model.object_roles:
        if role.name.lower() == search_name:
            return role
    msg = "Role '{0}' not found for {1}".format(role_name, type(model))
    raise ValueError(msg)


def set_roles(agent, model, role_names, endpoint='related_users', disassociate=False):
    """Associate a list of roles to a user/team for a given api page model

    :param agent: The api page model for a user/team
    :param model: A resource api page model with related roles endpoint
    :param role_names: A case insensitive list of role names
    :param endpoint: The endpoint to use when making the role association.
        - 'related_users': use the related users endpoint of the role
        - 'related_roles': use the related roles endpoint of the user
    :param disassociate: A boolean indicating whether to associate or
        disassociate the role with the user

    Usage::
        >>> # create a user that is an organization admin with use and
        >>> # update roles on a test inventory
        >>> foo_organization = factories.organization(name='foo')
        >>> bar_inventory = factories.inventory(name='bar')
        >>> test_user = factories.user()
        >>> set_roles(test_user, foo_organization, ['admin'])
        >>> set_roles(test_user, bar_inventory, ['use', 'update'])
    """
    object_roles = [get_role(model, name) for name in role_names]
    for role in object_roles:
        if endpoint == 'related_users':
            payload = {'id': agent.id}
            if isinstance(agent, User_Page):
                endpoint_model = role.get_related('users')
            elif isinstance(agent, Team_Page):
                endpoint_model = role.get_related('teams')
            else:
                raise ValueError("Unhandled type for agent - %s." % endpoint_model)
        elif endpoint == 'related_roles':
            payload = {'id': role.id}
            endpoint_model = agent.get_related('roles')
        else:
            raise RuntimeError('Invalid role association endpoint')
        if disassociate:
            payload['disassociate'] = disassociate
        with pytest.raises(towerkit.exceptions.NoContent):
            endpoint_model.post(payload)


# -----------------------------------------------------------------------------
# Integrated Assertion Helpers
# -----------------------------------------------------------------------------

def check_role_association(user, model, role_name):
    # check the related users endpoint of the role for user
    role = get_role(model, role_name)
    results = role.get_related('users').get(username=user.username)
    if results.count != 1:
        msg = 'Unable to verify {0} {1} role association'
        pytest.fail(msg.format(type(model), role_name))


def check_role_disassociation(user, model, role_name):
    # check the related users endpoint of the role for absence of user
    role = get_role(model, role_name)
    results = role.get_related('users').get(username=user.username)
    if results.count != 0:
        msg = 'Unable to verify {0} {1} role disassociation'
        pytest.fail(msg.format(type(model), role_name))


def check_request(model, method, code, data=None):
    """Make an HTTP request and check the response payload against the provided
    http response code
    """
    method = method.lower()
    api = model.api
    url = model.base_url.format(**model.json)

    if method in ('get', 'head', 'options', 'delete'):
        if data:
            log.warning('Unused {0} request data provided'.format(method))
        response = getattr(api, method)(url)
    else:
        response = getattr(api, method)(url, data)
    if response.status_code != code:
        msg = 'Unexpected {0} request response code: {1} != {2}'
        pytest.fail(msg.format(method, response.status_code, code))


def assert_response_raised(tower_object, response=httplib.OK):
    """Check PUT, PATCH, and DELETE against a Tower resource.
    """
    exc_dict = {
        httplib.OK: None,
        httplib.NOT_FOUND: towerkit.exceptions.NotFound,
        httplib.FORBIDDEN: towerkit.exceptions.Forbidden,
    }
    exc = exc_dict[response]
    for method in ('put', 'patch', 'delete'):
        if exc is None:
            getattr(tower_object, method)()
        else:
            with pytest.raises(exc):
                getattr(tower_object, method)()


def check_read_access(tower_object, expected_forbidden=[], unprivileged=False):
    """Check GET against a Tower resource.
    """
    # for test scenarios involving unprivileged users
    if unprivileged:
        with pytest.raises(towerkit.exceptions.Forbidden):
            tower_object.get()
    # for test scenarios involving privileged users
    else:
        tower_object.get()
        for related in tower_object.related:
            if related in expected_forbidden:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    tower_object.get_related(related)
            else:
                tower_object.get_related(related)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def get_nt_endpoints(notifiable_resource):
    '''
    Helper function that returns the notification template endpoints of a
    notifiable Tower resource.
    '''
    nt_any_pg = notifiable_resource.get_related('notification_templates_any')
    nt_success_pg = notifiable_resource.get_related('notification_templates_success')
    nt_error_pg = notifiable_resource.get_related('notification_templates_error')
    if notifiable_resource.type == 'organization':
        nt_pg = notifiable_resource.get_related('notification_templates')
        return [nt_pg, nt_any_pg, nt_success_pg, nt_error_pg]
    else:
        return [nt_any_pg, nt_success_pg, nt_error_pg]


def set_read_role(user_pg, notifiable_resource):
    '''
    Helper function that grants a user the read_role of a notifiable_resource.
    '''
    if notifiable_resource.type == 'inventory_source':
        inventory_pg = notifiable_resource.get_related('inventory')
        set_roles(user_pg, inventory_pg, ['read'])
    else:
        set_roles(user_pg, notifiable_resource, ['read'])


def check_user_capabilities(resource, role):
    """Helper function used in checking the values of summary_fields flag, 'user_capabilities'
    """
    assert resource.summary_fields['user_capabilities'] == user_capabilities[resource.type][role], \
        "Unexpected response for 'user_capabilities' when testing against a[n] %s resource with a user with %s permissions." \
        % (resource.type, role)
    # if given an inventory, additionally check child groups and hosts
    # child groups/hosts should have the same value for 'user_capabilities' as their inventory
    if resource.type == 'inventory':
        groups_pg = resource.get_related('groups')
        for group in groups_pg.results:
            assert group.summary_fields['user_capabilities'] == user_capabilities['group'][role], \
                "Unexpected response for 'user_capabilities' when testing groups with a user with inventory-%s." % role
        hosts_pg = resource.get_related('hosts')
        for host in hosts_pg.results:
            assert host.summary_fields['user_capabilities'] == user_capabilities['host'][role], \
                "Unexpected response for 'user_capabilities' when testing hosts with a user with inventory-%s." % role


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize('endpoint', ['related_users', 'related_roles'])
@pytest.mark.parametrize(
    'resource_name',
    ['organization', 'team', 'project', 'inventory', 'inventory_script', 'credential', 'job_template']
)
def test_role_association_and_disassociation(factories, resource_name, endpoint):
    """Verify basic role association and disassociation functionality.
    """
    resource = getattr(factories, resource_name)()
    # make credential and user organization align in testing credentials
    if resource.type == 'credential':
        user = factories.user(organization=resource.get_related('organization'))
    else:
        user = factories.user()
    for role in resource.object_roles:
        role_name = role.name
        # associate the role with the user
        set_roles(user, resource, [role_name], endpoint=endpoint)
        check_role_association(user, resource, role_name)
        # disassociate the role from the user
        set_roles(user, resource, [role_name], endpoint=endpoint, disassociate=True)
        check_role_disassociation(user, resource, role_name)


@pytest.mark.parametrize('endpoint', ['related_users', 'related_roles'])
@pytest.mark.parametrize(
    'resource_name, initial_role, unauthorized_target_role',
    [
        ('organization', 'member', 'admin'),
        ('team', 'read', 'admin'),
        ('project', 'read', 'admin'),
        ('inventory', 'read', 'admin'),
        ('inventory_script', 'read', 'admin'),
        ('credential', 'read', 'admin'),
        ('job_template', 'read', 'admin'),
    ]
)
def test_unauthorized_self_privilege_escalation_returns_code_403(
        factories, auth_user, endpoint,
        resource_name, initial_role, unauthorized_target_role):
    """A user with [intial_role] permission on a [resource_name] cannot add
    the [unauthorized_target_role] for the [resource_name] to themselves
        """
    # make credential and user organization align in testing credentials
    if resource_name == 'credential':
        organization = factories.organization()
        user = factories.user(organization=organization)
        resource = getattr(factories, resource_name)(organization=organization)
    else:
        user = factories.user()
        resource = getattr(factories, resource_name)()
    # make a test user and associate it with the initial role
    set_roles(user, resource, [initial_role])
    with auth_user(user), pytest.raises(towerkit.exceptions.Forbidden):
        set_roles(user, resource, [unauthorized_target_role], endpoint=endpoint)


@pytest.mark.parametrize('payload_resource_roles, response_codes', [
    (
        {'credential': ['read'], 'inventory': ['use'], 'project': ['use']},
        {'PATCH': httplib.FORBIDDEN, 'PUT': httplib.FORBIDDEN}
    ),
    (
        {'credential': ['use'], 'inventory': ['read'], 'project': ['use']},
        {'PATCH': httplib.FORBIDDEN, 'PUT': httplib.FORBIDDEN}
    ),
    (
        {'credential': ['use'], 'inventory': ['use'], 'project': ['read']},
        {'PATCH': httplib.FORBIDDEN, 'PUT': httplib.FORBIDDEN}
    ),
    (
        {'credential': ['use'], 'inventory': ['use'], 'project': ['use']},
        {'PATCH': httplib.OK, 'PUT': httplib.OK}
    ),
])
def test_job_template_change_request_without_usage_role_returns_code_403(
        auth_user, factories, payload_resource_roles, response_codes):
    """Verify that a user cannot change the related project, inventory, or
    credential of a job template unless they have usage permissions on all
    three resources and are admins of the job template
    """
    user = factories.user()
    organization = factories.organization()
    job_template = factories.job_template(organization=organization)
    set_roles(user, organization, ['member'])
    set_roles(user, job_template, ['admin'])
    # generate test request payload
    data, resources = factories.job_template.payload(
        organization=organization)
    # assign test permissions
    for name, roles in payload_resource_roles.iteritems():
        set_roles(user, resources[name], roles)
    # check access
    for method, code in response_codes.iteritems():
        with auth_user(user):
            check_request(job_template, method, code, data=data)


def test_job_template_creators_are_added_to_admin_role(
        factories, auth_user, api_job_templates_pg):
    """Verify that job template creators are added to the admin role of the
    created job template
    """
    # make test user
    user = factories.user()
    # generate job template test payload
    data, resources = factories.job_template.payload()
    # set user resource role associations
    set_roles(user, resources['organization'], ['admin'])
    for name in ('credential', 'project', 'inventory'):
        set_roles(user, resources[name], ['use'])
    # create a job template as the test user
    with auth_user(user):
        job_template = api_job_templates_pg.post(data)
    # verify succesful job_template admin role association
    check_role_association(user, job_template, 'admin')


def test_job_template_post_request_without_network_credential_access(
        factories, auth_user, api_job_templates_pg):
    """Verify that job_template post requests with network credentials in
    the payload are only permitted if the user making the request has usage
    permission for the network credential.
    """
    # set user resource role associations
    data, resources = factories.job_template.payload()
    organization = resources['organization']
    user = factories.user(organization=organization)
    for name in ('credential', 'project', 'inventory'):
        set_roles(user, resources[name], ['use'])
    # make network credential and add it to payload
    network_credential = factories.credential(kind='net', organization=organization)
    data['network_credential'] = network_credential.id
    # check POST response code with network credential read permissions
    set_roles(user, network_credential, ['read'])
    with auth_user(user):
        check_request(api_job_templates_pg, 'POST', httplib.FORBIDDEN, data)
    # add network credential usage role permissions to test user
    set_roles(user, network_credential, ['use'])
    # verify that the POST request is now permitted
    with auth_user(user):
        check_request(api_job_templates_pg, 'POST', httplib.CREATED, data)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Organization_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user should not be able to:
        * Issue GETs to our organization details page
        * Issue GETs to all of this organization's related pages
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.FORBIDDEN)

    def test_auditor_role(self, factories, user_password):
        '''
        A user with organization 'auditor' should be able to:
        * Issue GETs to our organization details page
        * Issue GETs to all of this organization's related pages

        A user with organization 'auditor' should not be able to:
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user auditor privileges
        set_roles(user_pg, organization_pg, ['auditor'])

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.FORBIDDEN)

    def test_admin_role(self, factories, user_password):
        '''
        A user with organization 'admin' should be able to:
        * GET our organization details page
        * GET all of our organization's related pages
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user admin privileges
        set_roles(user_pg, organization_pg, ['admin'])

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.OK)

    def test_member_role(self, factories, user_password):
        '''
        A user with organization 'member' should be able to:
        * The ability to make a GET to our target organization
        * The ability to make a GET against our organization's related endpoints

        A user with organization 'member' should not be able to:
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user member privileges
        set_roles(user_pg, organization_pg, ['member'])

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.FORBIDDEN)

    def test_read_role(self, factories, user_password):
        '''
        A user with organization 'read' should be able to:
        * The ability to make a GET to our target organization
        * The ability to make a GET against our organization's related endpoints

        A user with organization 'read' should not be able to:
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user read role privileges
        set_roles(user_pg, organization_pg, ['read'])

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(organization_pg)

            # check put/patch/delete
            assert_response_raised(organization_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'auditor', 'member', 'read'])
    def test_user_capabilities(self, factories, user_password, api_organizations_pg, role):
        """Test user_capabilities given each organization role."""
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, organization_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(organization_pg.get(), role)
            check_user_capabilities(api_organizations_pg.get(id=organization_pg.id).results.pop().get(), role)

    def test_member_role_association(self, factories, user_password):
        '''
        Tests that after a user is granted member_role that he now shows
        up under organizations/N/users.
        '''
        user_pg = factories.user()
        organization_pg = factories.organization()

        # organization by default should have no users
        users_pg = organization_pg.get_related('users')
        assert users_pg.count == 0, "%s user[s] unexpectedly found for organization/%s." % (users_pg.count, organization_pg.id)

        # give test user member role privileges
        set_roles(user_pg, organization_pg, ["member"])

        # assert that organizations/N/users now shows test user
        assert users_pg.get().count == 1, "Expected one user for organization/%s/users/, got %s." % (organization_pg.id, users_pg.count)
        assert users_pg.results[0].id == user_pg.id, \
            "Organization user not our target user. Expected user with ID %s but got one with ID %s." % (user_pg.id, users_pg.results[0].id)

    def test_autopopulated_member_role(self, organization, org_user, user_password):
        '''
        Tests that when you create a user by posting to organizations/N/users
        that the user is automatically created with a member_role for this
        organization.
        '''
        # assert test user created in target organization
        organizations_pg = org_user.get_related('organizations')
        assert organizations_pg.count == 1, \
            "Unexpected number of organizations returned. Expected 1, got %s." % organizations_pg.count
        assert organizations_pg.results[0].id == organization.id, \
            "org_user not created in organization/%s." % organization.id

        # assert test user created with member_role
        roles_pg = org_user.get_related('roles')
        assert roles_pg.count == 1, \
            "Unexpected number of roles returned. Expected 1, got %s." % roles_pg.count
        role_pg = roles_pg.results[0]
        assert role_pg.id == organization.get_object_role('member_role').id, \
            "Unexpected user role returned. Expected %s, got %s." % (organization.get_object_role('member_role').id, role_pg.id)

    @pytest.mark.parametrize('organization_role', ['admin_role', 'auditor_role', 'member_role', 'read_role'])
    def test_organization_roles_not_allowed_with_teams(self, factories, organization_role):
        '''
        Test that an organization role association with a team raises a 400.
        '''
        team_pg = factories.team()
        organization_pg = factories.organization()

        # attempt role association
        role_pg = organization_pg.get_object_role(organization_role)
        payload = dict(id=role_pg.id)

        exc_info = pytest.raises(towerkit.exceptions.BadRequest, team_pg.get_related('roles').post, payload)
        result = exc_info.value[1]
        assert result == {u'msg': u'You cannot assign an Organization role as a child role for a Team.'}, \
            "Unexpected error message received when attempting to assign an organization role to a team."


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Project_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user/team should not be able to:
        * GET our project detail page
        * GET all project related pages
        * Launch project updates
        * Edit our project
        * Delete our project
        '''
        project_pg = factories.project()
        user_pg = factories.user()
        update_pg = project_pg.get_related('update')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, unprivileged=True)

            # check project update
            with pytest.raises(towerkit.exceptions.Forbidden):
                update_pg.post()

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/3930")
    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with project 'admin' should be able to:
        * GET our project detail page
        * GET all project related pages
        * Edit our project
        * Delete our project
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, project_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with project 'update' should be able to:
        * GET our project detail page
        * GET all project related pages

        A user/team with project 'update' should not be able to:
        * Edit our project
        * Delete our project
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent update_role
        set_test_roles(user_pg, project_pg, agent, "update")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with project 'use' should be able to:
        * GET our project detail page
        * GET all project related pages

        A user/team with project 'use' should not be able to:
        * Edit our project
        * Delete our project
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent use_role
        set_test_roles(user_pg, project_pg, agent, "use")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with project 'read' should be able to:
        * GET our project detail page
        * GET all project related pages

        A user/team with project 'read' should not be able to:
        * Edit our project
        * Delete our project
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, project_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_user_capabilities(self, factories, user_password, api_projects_pg, role):
        """Test user_capabilities given each project role."""
        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(project_pg.get(), role)
            check_user_capabilities(api_projects_pg.get(id=project_pg.id).results.pop().get(), role)

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_launch_update(self, factories, user_password, role):
        """Tests ability to launch a project update."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'read']

        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg = project_pg.update().wait_until_completed()
                assert update_pg.is_successful, "Project update unsuccessful - %s." % update_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    project_pg.update()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_cancel_update(self, factories, project_ansible_git_nowait, user_password, role):
        """Tests project update cancellation. Project admins can cancel other people's projects."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'read']

        user_pg = factories.user()
        update_pg = project_ansible_git_nowait.related.current_update.get()

        # give test user target role privileges
        set_roles(user_pg, project_ansible_git_nowait, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update_pg.cancel()
                # wait for project to finish to ensure clean teardown
                update_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4181')
    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_delete_update(self, factories, user_password, role):
        """Tests ability to delete a project update."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'read']

        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        # launch project update
        update_pg = project_pg.update()

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg.delete()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update_pg.delete()
                # wait for project to finish to ensure clean teardown
                update_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_update_user_capabilities(self, factories, user_password, api_project_updates_pg, role):
        """Test user_capabilities given each project role on spawned
        project_updates."""
        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        # launch project_update
        update_pg = project_pg.update().wait_until_completed()

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(update_pg.get(), role)
            check_user_capabilities(api_project_updates_pg.get(id=update_pg.id).results.pop().get(), role)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Credential_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user/team should not be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        * Edit the credential
        * Delete the credential
        '''
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with credential 'admin' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        * Edit the credential
        * Delete the credential
        '''
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        # give agent admin_role
        set_test_roles(user_pg, credential_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg)

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with credential 'use' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related

        A user/team with credential 'use' should not be able to:
        * Edit the credential
        * Delete the credential
        '''
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        # give agent use_role
        set_test_roles(user_pg, credential_pg, agent, "use")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg, ['user'])

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with credential 'read' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related

        A user/team with credential 'read' should not be able to:
        * Edit the credential
        * Delete the credential
        '''
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        # give agent read_role
        set_test_roles(user_pg, credential_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg, ['user'])

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'use', 'read'])
    def test_user_capabilities(self, factories, user_password, api_credentials_pg, role):
        """Test user_capabilities given each credential role."""
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        # give test user target role privileges
        set_roles(user_pg, credential_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(credential_pg.get(), role)
            check_user_capabilities(api_credentials_pg.get(id=credential_pg.id).results.pop().get(), role)

    def test_autopopulated_admin_role_with_users(self, factories):
        '''
        Tests that when you create a credential with a value supplied for 'user'
        that your user is automatically given the admin role of your credential.
        '''
        user_pg = factories.user()

        # assert newly created user has no roles
        assert not user_pg.get_related('roles').count, \
            "Newly created user created unexpectedly with roles - %s." % user_pg.get_related('roles')

        # assert user now has admin role after user credential creation
        credential_pg = factories.credential(user=user_pg, organization=None)
        admin_role_users_pg = credential_pg.get_object_role('admin_role').get_related('users')
        assert admin_role_users_pg.count == 1, \
            "Unexpected number of users with our credential admin role. Expected one, got %s." % admin_role_users_pg.count
        assert admin_role_users_pg.results[0].id == user_pg.id, \
            "Unexpected admin role user returned. Expected user with ID %s, but %s." % (user_pg.id, admin_role_users_pg.results[0].id)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3392')
    def test_user_credential_role_assignment(self, factories, set_roles):
        '''Tests that user credential roles may not be given to other users and teams.'''
        # create user credential
        user = factories.user()
        credential = factories.credential(user=user, organization=None)
        # create another user and team
        another_user = factories.user()
        team = factories.team()
        # assert that credential roles may not be assigned to these agents
        role_names = [role.replace("_role", "") for role in credential.summary_fields.object_roles.keys()]
        for role_name in role_names:
            with pytest.raises(towerkit.exceptions.BadRequest):
                set_roles(another_user, credential, [role_name])
            with pytest.raises(towerkit.exceptions.BadRequest):
                set_roles(team, credential, [role_name])

    def test_invalid_organization_credential_role_assignment(self, factories, set_roles):
        '''
        Tests that organization credentials may not have their roles assigned to users
        and teams who exist outside of their organization.
        '''
        # create an organization credential
        organization = factories.organization()
        credential = factories.credential(organization=organization)
        # user from another organization may not be assigned any of our credential roles
        another_organization = factories.organization()
        user = factories.user(organization=another_organization)
        role_names = [role.replace("_role", "") for role in credential.summary_fields.object_roles.keys()]
        for role_name in role_names:
            with pytest.raises(towerkit.exceptions.BadRequest):
                set_roles(user, credential, [role_name])
        # team from another organization may not be assigned any of our credential roles
        team = factories.team(organization=another_organization)
        for role_name in role_names:
            with pytest.raises(towerkit.exceptions.BadRequest):
                set_roles(team, credential, [role_name])

    def test_valid_organization_credential_role_assignment(self, factories, set_roles):
        '''
        Tests that organization credentials may have their roles assigned to users
        and teams who exist within their own organization.
        '''
        # create an organization credential
        organization = factories.organization()
        credential = factories.credential(organization=organization)
        # user from another organization may be assigned our credential roles
        user = factories.user(organization=organization)
        role_names = [role.replace("_role", "") for role in credential.summary_fields.object_roles.keys()]
        for role_name in role_names:
            set_roles(user, credential, [role_name])
        # team from another organization may be assigned our credential roles
        team = factories.team(organization=organization)
        for role_name in role_names:
            set_roles(team, credential, [role_name])


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Team_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user/team may not be able to:
        * Get the team details page
        * Get all of the team related pages
        * Edit the team
        * Delete the team
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(team_pg, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(team_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with team 'admin_role' should be able to:
        * Get the team details page
        * Get all of the team related pages
        * Edit the team
        * Delete the team
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, team_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(team_pg, ['organization'])

            # check put/patch/delete
            assert_response_raised(team_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_member_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with team 'member_role' should be able to:
        * Get the team details page
        * Get all of the team related pages

        A user/team with team 'member_role' should not be able to:
        * Edit the team
        * Delete the team
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        # give agent member_role
        set_test_roles(user_pg, team_pg, agent, "member")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(team_pg, ['organization'])

            # check put/patch/delete
            assert_response_raised(team_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with team 'read_role' should be able to:
        * Get the team details page
        * Get all of the team related pages

        A user/team with team 'read_role' should not be able to:
        * Edit the team
        * Delete the team
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, team_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(team_pg, ['organization'])

            # check put/patch/delete
            assert_response_raised(team_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'member', 'read'])
    def test_user_capabilities(self, factories, user_password, api_teams_pg, role):
        """Test user_capabilities given each team role."""
        team_pg = factories.team()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, team_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(team_pg.get(), role)
            check_user_capabilities(api_teams_pg.get(id=team_pg.id).results.pop().get(), role)

    def test_member_role_association(self, factories, user_password):
        '''
        Tests that after a user is granted member_role that he now shows
        up under teams/N/users.
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        # team by default should have no users
        users_pg = team_pg.get_related('users')
        assert users_pg.count == 0, "%s user[s] unexpectedly found for teams/%s." % (users_pg.count, team_pg.id)

        # give test user member role privileges
        role_pg = team_pg.get_object_role('member_role')
        with pytest.raises(towerkit.exceptions.NoContent):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        # assert that teams/N/users now shows test user
        assert users_pg.get().count == 1, "Expected one user for teams/%s/users/, got %s." % (team_pg.id, users_pg.count)
        assert users_pg.results[0].id == user_pg.id, \
            "Team user not our target user. Expected user with ID %s but got one with ID %s." % (user_pg.id, users_pg.results[0].id)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory_Script_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, inventory_script, user_password):
        '''
        An unprivileged user/team may not be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related
        * Edit your inventory script
        * Delete your inventory script
        '''
        user_pg = factories.user()

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_script, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(inventory_script, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, inventory_script, set_test_roles, agent, user_password):
        '''
        A user/team with inventory_script 'admin' should be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related
        * Edit your inventory script
        * Delete your inventory script
        '''
        user_pg = factories.user()

        # assert value for 'script' present
        assert inventory_script.script
        script = inventory_script.script

        # give agent admin_role
        set_test_roles(user_pg, inventory_script, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_script, ["organization"])

            # check that value of 'script' viewable
            assert inventory_script.script == script, \
                "Unexpected value for 'script'; expected %s but got %s." % (script, inventory_script.script)

            # check put/patch/delete
            assert_response_raised(inventory_script, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, inventory_script, set_test_roles, agent, user_password):
        '''
        A user/team with inventory_script 'read' should be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related

        A user/team with inventory_script 'read' should not be able to:
        * Edit your inventory script
        * Delete your inventory script
        '''
        user_pg = factories.user()

        # assert value for 'script' present
        assert inventory_script.script

        # give agent read_role
        set_test_roles(user_pg, inventory_script, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_script, ["organization"])

            # check that value of 'script' not viewable
            assert not inventory_script.script, \
                "Unexpected value for 'script'; expected null but got %s." % inventory_script.script

            # check put/patch/delete
            assert_response_raised(inventory_script, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'read'])
    def test_user_capabilities(self, factories, inventory_script, user_password, api_inventory_scripts_pg, role):
        """Test user_capabilities given each inventory_script role."""
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, inventory_script, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(inventory_script.get(), role)
            check_user_capabilities(api_inventory_scripts_pg.get(id=inventory_script.id).results.pop().get(), role)

    def test_able_to_assign_inventory_script_to_different_org(self, factories, user_password, inventory_script, organization,
                                                              another_organization):
        '''
        Tests that org_admins can reassign an inventory_script to an organization for which they
        are an admin.
        '''
        user_pg = factories.user()
        set_roles(user_pg, organization, ['admin'])
        set_roles(user_pg, another_organization, ['admin'])

        # assert that org_admin can reassign label
        with self.current_user(user_pg.username, user_password):
            inventory_script.patch(organization=another_organization.id)

    def test_unable_to_assign_inventory_script_to_different_org(self, factories, user_password, inventory_script, organization,
                                                                another_organization):
        '''
        Tests that org_admins cannot reassign an inventory_script to an organization for which they
        are only a member.
        '''
        user_pg = factories.user()
        set_roles(user_pg, organization, ['admin'])
        set_roles(user_pg, another_organization, ['member'])

        # assert that org_admin cannot reassign label
        with self.current_user(user_pg.username, user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                inventory_script.patch(organization=another_organization.id)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user/team should not be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Launch the JT
        * Edit the JT
        * Delete the JT
        '''
        job_template_pg = factories.job_template()
        user_pg = factories.user()
        launch_pg = job_template_pg.get_related('launch')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(job_template_pg, unprivileged=True)

            # check JT launch
            with pytest.raises(towerkit.exceptions.Forbidden):
                launch_pg.post()

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with JT 'admin' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Edit the JT
        * Delete the JT
        '''
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, job_template_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(job_template_pg, ["credential", "inventory", "project"])

            # check put/patch/delete
            assert_response_raised(job_template_pg.get(), httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_execute_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with JT 'execute' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages

        A user/team with JT 'execute' should not be able to:
        * Edit the JT
        * Delete the JT
        '''
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give agent execute_role
        set_test_roles(user_pg, job_template_pg, agent, "execute")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(job_template_pg, ["credential", "inventory", "project"])

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with JT 'admin' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages

        A user/team with JT 'admin' should not be able to:
        * Edit the JT
        * Delete the JT
        '''
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, job_template_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(job_template_pg, ["credential", "inventory", "project"])

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_user_capabilities(self, factories, user_password, api_job_templates_pg, role):
        """Test user_capabilities given each job_template role."""
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(job_template_pg.get(), role)
            check_user_capabilities(api_job_templates_pg.get(id=job_template_pg.id).results.pop().get(), role)

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_launch_job(self, factories, user_password, role):
        """Tests ability to launch a job."""
        ALLOWED_ROLES = ['admin', 'execute']
        REJECTED_ROLES = ['read']

        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                job_pg = job_template_pg.launch().wait_until_completed()
                assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    job_template_pg.launch()
            else:
                raise ValueError("Received unhandled job_template role.")

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_relaunch_job(self, factories, user_password, role):
        """Tests ability to relaunch a job."""
        ALLOWED_ROLES = ['admin', 'execute']
        REJECTED_ROLES = ['read']

        job_template_pg = factories.job_template()
        user_pg = factories.user()
        job_pg = job_template_pg.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                relaunched_job_pg = job_pg.relaunch().wait_until_completed()
                assert relaunched_job_pg.is_successful, "Job unsuccessful - %s." % job_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    job_pg.relaunch()
            else:
                raise ValueError("Received unhandled job_template role.")

    def test_relaunch_with_ask_inventory(self, factories, job_template, user_password):
        '''Tests relaunch RBAC when ask_inventory_on_launch is true.'''
        # FIXME: update for when factories get fixed for #821
        job_template.get_related('inventory').delete()
        job_template.patch(ask_inventory_on_launch=True)

        credential = job_template.get_related('credential')
        inventory = factories.inventory()
        user1 = factories.user()
        user2 = factories.user()

        # set test permissions
        set_roles(user1, job_template, ['execute'])
        set_roles(user1, inventory, ['use'])
        set_roles(user1, credential, ['use'])
        set_roles(user2, job_template, ['execute'])

        # launch job as user1
        with self.current_user(username=user1.username, password=user_password):
            payload = dict(inventory=inventory.id)
            job_pg = job_template.launch(payload).wait_until_completed()

        # relaunch as user2 should raise 403
        with self.current_user(username=user2.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                job_pg.get_related('relaunch').post()

    def test_relaunch_with_ask_credential(self, factories, job_template_no_credential, user_password):
        '''Tests relaunch RBAC when ask_credential_on_launch is true.'''
        job_template_no_credential.patch(ask_credential_on_launch=True)

        credential = factories.credential()
        user1 = factories.user(organization=credential.get_related('organization'))
        user2 = factories.user()

        # set test permissions
        set_roles(user1, job_template_no_credential, ['execute'])
        set_roles(user1, credential, ['use'])
        set_roles(user2, job_template_no_credential, ['execute'])

        # launch job as user1
        with self.current_user(username=user1.username, password=user_password):
            payload = dict(credential=credential.id)
            job_pg = job_template_no_credential.launch(payload).wait_until_completed()

        # relaunch as user2 should raise 403
        with self.current_user(username=user2.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                job_pg.get_related('relaunch').post()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_cancel_job(self, factories, user_password, role):
        """Tests job cancellation. JT admins can cancel other people's jobs."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['execute', 'read']

        job_template_pg = factories.job_template(playbook='sleep.yml', extra_vars=dict(sleep_interval=10))
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        # launch job_template
        job_pg = job_template_pg.launch()

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                job_pg.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    job_pg.cancel()
                # wait for job to finish to ensure clean teardown
                job_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled job_template role.")

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4190')
    def test_delete_job_as_org_admin(self, factories, user_password):
        """Create a run and a scan JT and an org_admin for each of these JTs. Then check
        that each org_admin may only delete his org's job.

        Note: job deletion is organization scoped. A run JT's project determines its
        organization and a scan JT's inventory determines its organization.
        """
        # create two JTs
        run_job_template = factories.job_template()
        scan_job_template = factories.job_template(job_type="scan", project=None)

        # sanity check
        run_jt_org = run_job_template.get_related('project').get_related('organization')
        scan_jt_org = scan_job_template.get_related('inventory').get_related('organization')
        assert run_jt_org.id != scan_jt_org.id, "Test JTs unexpectedly in the same organization."

        # create org_admins
        org_admin1 = factories.user(organization=run_jt_org)
        org_admin2 = factories.user(organization=scan_jt_org)
        set_roles(org_admin1, run_jt_org, ['admin'])
        set_roles(org_admin2, scan_jt_org, ['admin'])

        # launch JTs
        run_job = run_job_template.launch()
        scan_job = scan_job_template.launch()

        # assert that each org_admin cannot delete other organization's job
        with self.current_user(username=org_admin1.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                scan_job.delete()
        with self.current_user(username=org_admin2.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                run_job.delete()

        # assert that each org_admin can delete his own organization's job
        with self.current_user(username=org_admin1.username, password=user_password):
            run_job.delete()
        with self.current_user(username=org_admin2.username, password=user_password):
            scan_job.delete()

    def test_delete_job_as_org_user(self, factories, user_password):
        """Tests ability to delete a job as a privileged org_user."""
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, ['admin'])

        # launch job_template
        job_pg = job_template_pg.launch()

        with self.current_user(username=user_pg.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                job_pg.delete()
            # wait for project to finish to ensure clean teardown
            job_pg.wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_job_user_capabilities(self, factories, user_password, api_jobs_pg, role):
        """Test user_capabilities given each JT role on spawned jobs."""
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, job_template_pg, [role])

        # launch job_template
        job_pg = job_template_pg.launch().wait_until_completed()

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(job_pg.get(), role)
            check_user_capabilities(api_jobs_pg.get(id=job_pg.id).results.pop().get(), role)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, host_local, aws_inventory_source, custom_group, user_password, factories):
        '''
        An unprivileged user should not be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        user_pg = factories.user()

        commands_pg = inventory_pg.get_related('ad_hoc_commands')
        inv_source_update_pg = aws_inventory_source.get_related('update')
        custom_group_update_pg = custom_group.get_related('inventory_source').get_related('update')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, unprivileged=True)

            # update aws_group
            with pytest.raises(towerkit.exceptions.Forbidden):
                inv_source_update_pg.post()

            # update custom group
            with pytest.raises(towerkit.exceptions.Forbidden):
                custom_group_update_pg.post()

            # post command
            with pytest.raises(towerkit.exceptions.Forbidden):
                commands_pg.post()

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post()
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post()

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(custom_group, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, host_local, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'admin' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, inventory_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            groups_pg.post(group_payload)
            hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.OK)
            assert_response_raised(group_pg, httplib.OK)
            assert_response_raised(inventory_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, host_local, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'use' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related

        A user/team with inventory 'use' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent use_role
        set_test_roles(user_pg, inventory_pg, agent, "use")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group_pg, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_adhoc_role(self, host_local, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'adhoc' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related

        A user/team with inventory 'adhoc' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent adhoc_role
        set_test_roles(user_pg, inventory_pg, agent, "ad hoc")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group_pg, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, host_local, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'update' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related

        A user/team with inventory 'update' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent update_role
        set_test_roles(user_pg, inventory_pg, agent, "update")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group_pg, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, host_local, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'read' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related

        A user/team with inventory 'read' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, inventory_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group_pg, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_user_capabilities(self, factories, user_password, api_inventories_pg, role):
        """Test user_capabilities given each inventory role."""
        inventory_pg = factories.inventory()
        factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(inventory_pg.get(), role)
            check_user_capabilities(api_inventories_pg.get(id=inventory_pg.id).results.pop().get(), role)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4098')
    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_custom_group(self, factories, custom_inventory_source, user_password, role):
        """Test ability to update a custom group."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = custom_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg = custom_inventory_source.update().wait_until_completed()
                assert update_pg.is_successful, "Update unsuccessful - %s." % update_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    custom_inventory_source.update()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_cloud_group(self, factories, aws_inventory_source, user_password, role):
        """Test ability to update a cloud group. Note: only tested on AWS to save time.
        Also, user should be able launch update even though cloud_credential is under
        admin user.
        """
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user_pg = factories.user()

        # give agent target role privileges
        inventory_pg = aws_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg = aws_inventory_source.update().wait_until_completed()
                assert update_pg.is_successful, "Update unsuccessful - %s." % update_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    aws_inventory_source.update()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_cancel_update(self, factories, aws_inventory_source, user_password, role):
        """Tests inventory update cancellation. Inventory admins can cancel other people's updates."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'ad hoc', 'read']

        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = aws_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        # launch inventory update
        update_pg = aws_inventory_source.update()

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update_pg.cancel()
                # wait for inventory update to finish to ensure clean teardown
                update_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4182')
    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_delete_update(self, factories, custom_inventory_source, user_password, role):
        """Tests ability to delete an inventory update."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['use', 'ad hoc', 'update', 'read']

        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = custom_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        # launch inventory update
        update_pg = custom_inventory_source.update()

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg.delete()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update_pg.delete()
                # wait for inventory update to finish to ensure clean teardown
                update_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_update_user_capabilities(self, factories, custom_inventory_source, user_password, api_inventory_updates_pg, role):
        """Test user_capabilities given each inventory role on spawned
        inventory_updates."""
        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = custom_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        # launch inventory_update
        update_pg = custom_inventory_source.update().wait_until_completed()

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(update_pg.get(), role)
            check_user_capabilities(api_inventory_updates_pg.get(id=update_pg.id).results.pop().get(), role)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_launch_command(self, factories, user_password, role):
        """Test ability to launch a command."""
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'update', 'read']

        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # create command fixtures
        ad_hoc_commands_pg = inventory_pg.get_related('ad_hoc_commands')
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_name="ping")

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                command_pg = ad_hoc_commands_pg.post(payload).wait_until_completed()
                assert command_pg.is_successful, "Command unsuccessful - %s." % command_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    ad_hoc_commands_pg.post(payload)
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_relaunch_command(self, factories, user_password, role):
        """Tests ability to relaunch a command."""
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'update', 'read']

        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # launch command
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_name="ping")
        command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload).wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s." % command_pg

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                relaunched_command = command_pg.relaunch().wait_until_completed()
                assert relaunched_command.is_successful, "Command unsuccessful - %s." % command_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    command_pg.relaunch()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_cancel_command(self, factories, user_password, role):
        """Tests command cancellation. Inventory admins can cancel other people's commands."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['ad hoc', 'use', 'update', 'read']

        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        # launch command
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_args="sleep 10")
        command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload)

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                command_pg.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    command_pg.cancel()
            else:
                raise ValueError("Received unhandled inventory role.")

    def test_delete_command_as_org_admin(self, factories, user_password):
        """Create two ad hoc commands and an org_admin for each of these commands.
        Then check that each org_admin may only delete his org's command.

        Note: command deletion is organization scoped. A command's inventory determines
        its organization.
        """
        # create items for command payloads
        inventory1 = factories.inventory()
        inventory2 = factories.inventory()
        inv_org1 = inventory1.get_related('organization')
        inv_org2 = inventory2.get_related('organization')
        credential1 = factories.credential(organization=inv_org1)
        credential2 = factories.credential(organization=inv_org2)

        # sanity check
        assert inv_org1.id != inv_org2, "Test inventories unexpectedly in the same organization."

        # create org_admins
        org_admin1 = factories.user()
        org_admin2 = factories.user()
        set_roles(org_admin1, inv_org1, ['admin'])
        set_roles(org_admin2, inv_org2, ['admin'])

        # launch both commands
        payload = dict(inventory=inventory1.id,
                       credential=credential1.id,
                       module_name="ping")
        command1 = inventory1.get_related('ad_hoc_commands').post(payload)
        payload = dict(inventory=inventory2.id,
                       credential=credential2.id,
                       module_name="ping")
        command2 = inventory2.get_related('ad_hoc_commands').post(payload)

        # assert that each org_admin cannot delete other organization's command
        with self.current_user(username=org_admin1.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command2.delete()
        with self.current_user(username=org_admin2.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command1.delete()

        # assert that each org_admin can delete his own organization's command
        with self.current_user(username=org_admin1.username, password=user_password):
            command1.delete()
        with self.current_user(username=org_admin2.username, password=user_password):
            command2.delete()

    def test_delete_command_as_org_user(self, factories, user_password):
        """Tests ability to delete an ad hoc command as a privileged org_user."""
        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, ['admin'])

        # launch command
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_name="ping")
        command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload)

        with self.current_user(username=user_pg.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command_pg.delete()
            # wait for ad hoc command to finish to ensure clean teardown
            command_pg.wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_command_user_capabilities(self, factories, user_password, api_ad_hoc_commands_pg, role):
        """Test user_capabilities given each inventory role on spawned
        ad hoc commands."""
        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        # launch command
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_name="ping")
        command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload).wait_until_completed()

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(command_pg.get(), role)
            check_user_capabilities(api_ad_hoc_commands_pg.get(id=command_pg.id).results.pop().get(), role)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Notification_Template_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_notification_template_create_as_unprivileged_user(self, email_notification_template_payload, api_notification_templates_pg,
                                                               unprivileged_user, user_password):
        '''
        Tests that unprivileged users may not create notification templates.
        '''
        # test notification template create as unprivileged user
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                api_notification_templates_pg.post(email_notification_template_payload)

    def test_notification_template_create_as_org_admin(self, email_notification_template_payload, api_notification_templates_pg, org_admin, user_password):
        '''
        Tests that org_admins may create notification templates.
        '''
        # test notification template create as org_admin
        with self.current_user(username=org_admin.username, password=user_password):
            api_notification_templates_pg.post(email_notification_template_payload)

    def test_notification_template_associate_as_unprivileged_user(self, email_notification_template, notifiable_resource,
                                                                  unprivileged_user, user_password):
        '''
        Tests that unprivileged users may not associate a NT with a notifiable resource.
        '''
        # store our future test endpoints
        endpoints = get_nt_endpoints(notifiable_resource)

        # give our test user 'read' permissions
        set_read_role(unprivileged_user, notifiable_resource)

        # test notification template associate as unprivileged user
        payload = dict(id=email_notification_template.id)
        with self.current_user(username=unprivileged_user.username, password=user_password):
            for endpoint in endpoints:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    endpoint.post(payload)

    def test_notification_template_associate_as_org_admin(self, email_notification_template, notifiable_resource, org_admin, user_password):
        '''
        Tests that org_admins may associate a NT with a notifiable resource.
        '''
        # store our future test endpoints
        endpoints = get_nt_endpoints(notifiable_resource)

        # test notification template associate as org_admin
        payload = dict(id=email_notification_template.id)
        with self.current_user(username=org_admin.username, password=user_password):
            for endpoint in endpoints:
                with pytest.raises(towerkit.exceptions.NoContent):
                    endpoint.post(payload)

    def test_notification_template_read_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        '''
        Tests that unprivileged users cannot read NT endpoints.
        '''
        # assert that we cannot access api/v1/notification_templates
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.get()

    def test_notification_template_read_as_org_admin(self, email_notification_template, org_admin, user_password):
        '''
        Tests that org_admins can read NT endpoints.
        '''
        # assert that we can access api/v1/notification_templates
        with self.current_user(username=org_admin.username, password=user_password):
            email_notification_template.get()

    def test_notification_template_edit_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        '''
        Tests that unprivileged users cannot edit NTs.
        '''
        # assert that put/patch is forbidden
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.patch()

    def test_notification_template_edit_as_org_admin(self, email_notification_template, org_admin, user_password):
        '''
        Tests that org_admins can edit NTs.
        '''
        # assert that put/patch is accepted
        with self.current_user(username=org_admin.username, password=user_password):
            email_notification_template.put()
            email_notification_template.patch()

    def test_notification_template_delete_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        '''
        Tests that unprivileged_users cannot delete NTs.
        '''
        # assert that delete is forbidden
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.delete()

    def test_notification_template_delete_as_org_admin(self, email_notification_template, org_admin, user_password):
        '''
        Tests that org_admins can delete NTs.
        '''
        # assert that delete is accepted
        with self.current_user(username=org_admin.username, password=user_password):
            email_notification_template.delete()

    def test_user_capabilities_as_superuser(self, email_notification_template, api_notification_templates_pg):
        '''
        Tests NT 'user_capabilities' as superuser.
        '''
        check_user_capabilities(email_notification_template.get(), "superuser")
        check_user_capabilities(api_notification_templates_pg.get(id=email_notification_template.id).results.pop().get(), "superuser")

    def test_user_capabilities_as_org_admin(self, email_notification_template, org_admin, user_password, api_notification_templates_pg):
        '''
        Tests NT 'user_capabilities' as an org_admin.
        '''
        with self.current_user(username=org_admin.username, password=user_password):
            check_user_capabilities(email_notification_template.get(), "org_admin")
            check_user_capabilities(api_notification_templates_pg.get(id=email_notification_template.id).results.pop().get(), "org_admin")


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Notifications_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_notification_read_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        '''
        Test that unprivileged users cannot read notifications.
        '''
        notification_pg = email_notification_template.test().wait_until_completed()

        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                notification_pg.get()

    def test_notification_read_as_org_admin(self, email_notification_template, org_admin, user_password):
        '''
        Test that org_admins can read notifications.
        '''
        notification_pg = email_notification_template.test().wait_until_completed()

        with self.current_user(username=org_admin.username, password=user_password):
            notification_pg.get()

    def test_notification_test_as_unprivileged_user(self, email_notification_template, unprivileged_user,
                                                    user_password):
        '''Confirms that unprivileged users cannot test notifications.'''
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.test().wait_until_completed()

    def test_notification_test_as_another_org_admin(self, email_notification_template, another_org_admin,
                                                    user_password):
        """Confirms that admins of other orgs cannot test notifcations outside their organization"""
        with self.current_user(username=another_org_admin.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.test().wait_until_completed()


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Label_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.parametrize('role', ['admin', 'auditor', 'read', 'member'])
    def test_organization_label_post(self, factories, user_password, api_labels_pg, role):
        '''
        Users with organization 'admin' and 'member' should be able to create a label with their role
        organization. Users with organization 'auditor' and 'read' should receive a 403 forbidden.
        '''
        ALLOWED_ROLES = ['admin', 'member']
        REJECTED_ROLES = ['read', 'auditor']

        user_pg = factories.user()
        organization_pg = factories.organization()
        payload = factories.label.payload(organization=organization_pg)[0]

        # assert initial label post raises 403
        with self.current_user(username=user_pg.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                api_labels_pg.post(payload)

        # grant user target organization permission
        set_roles(user_pg, organization_pg, [role])

        # assert label post accepted
        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                api_labels_pg.post(payload)
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    api_labels_pg.post(payload)
            else:
                raise ValueError("Received unhandled organization role.")

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3592')
    @pytest.mark.parametrize("role", ["admin", "read"])
    def test_job_template_label_association(self, factories, user_password, role):
        '''
        Tests that when JT can_edit is true that our test user may associate a label with
        a JT. Note: our test iterates through "admin_role" and "read_role" since these two
        roles should unlock can_edit as true and false respectively.
        '''
        job_template_pg = factories.job_template()
        labels_pg = job_template_pg.get_related('labels')
        organization_pg = job_template_pg.get_related('inventory').get_related('organization')
        user_pg = factories.user(organization=organization_pg)
        label_pg = factories.label(organization=organization_pg)

        # grant user target JT permission
        set_roles(user_pg, job_template_pg, [role])

        # test label association
        payload = dict(id=label_pg.id)
        with self.current_user(username=user_pg.username, password=user_password):
            job_template_pg.get()
            if job_template_pg.summary_fields.user_capabilities.edit:
                with pytest.raises(towerkit.exceptions.NoContent):
                    labels_pg.post(payload)
            else:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    labels_pg.post(payload)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_User_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_user_admin_role_application_forbidden(self, factories, api_roles_pg):
        """Confirms that users are not able to have any admin role (dis)associated with themselves."""
        user_one, user_two = [factories.user() for _ in range(2)]
        user_one_admin_role = api_roles_pg.get(object_id=user_one.id,
                                               role_field='admin_role',
                                               members__in=user_one.id).results[0]

        for user in [user_one, user_two]:
            for disassociate in [True, False]:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    user.get_related('roles').post(dict(id=user_one_admin_role.id,
                                                        disassociate=disassociate))

    def test_user_capabilities_as_superuser(self, factories, api_users_pg):
        """Tests 'user_capabilities' with a superuser."""
        superuser = factories.user(is_superuser=True)

        check_user_capabilities(superuser.get(), "superuser")
        check_user_capabilities(api_users_pg.get(id=superuser.id).results.pop().get(), "superuser")

    def test_user_capabilities_as_org_admin(self, factories, user_password, api_users_pg):
        """Tests 'user_capabilities' with an org_admin."""
        organization = factories.organization()
        org_user = factories.user()
        org_admin = factories.user()
        set_roles(org_user, organization, ["member"])
        set_roles(org_admin, organization, ["admin"])

        with self.current_user(username=org_admin.username, password=user_password):
            check_user_capabilities(org_user.get(), "org_admin")
            check_user_capabilities(api_users_pg.get(id=org_user.id).results.pop().get(), "org_admin")


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_System_Jobs_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_as_superuser(self, system_job):
        '''
        Verify that a superuser account is able to GET a system_job resource.
        '''
        system_job.get()

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_as_non_superuser(self, non_superusers, user_password, api_system_jobs_pg, system_job):
        '''
        Verify that non-superuser accounts are unable to access a system_job.
        '''
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    api_system_jobs_pg.get(id=system_job.id)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3576')
    def test_user_capabilities_as_superuser(self, cleanup_jobs_with_status_completed, api_system_jobs_pg):
        '''
        Verify 'user_capabilities' with a superuser.
        '''
        check_user_capabilities(cleanup_jobs_with_status_completed.get(), "superuser")
        check_user_capabilities(api_system_jobs_pg.get(id=cleanup_jobs_with_status_completed.id).results.pop().get(), "superuser")


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Schedules_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_crud_as_superuser(self, resource_with_schedule):
        """Tests schedule CRUD as superuser against all UJTs that support schedules.
        Create is tested upon fixture instantiation."""
        # test get
        # NOTE: additional filter so that we do not delete our prestocked system job schedule
        schedule_pg = resource_with_schedule.get_related('schedules', not__name='Cleanup Job Schedule').results[0]
        # test put/patch
        schedule_pg.put()
        schedule_pg.patch()
        # test delete
        schedule_pg.delete()

    def test_crud_as_org_admin(self, org_admin, user_password, schedulable_resource_as_org_admin):
        """Tests schedules CRUD as an org_admin against an inventory_source, project, and JT."""
        schedules_pg = schedulable_resource_as_org_admin.get_related('schedules')
        payload = dict(name="Schedule - %s" % fauxfactory.gen_utf8(),
                       rrule="DTSTART:20160926T040000Z RRULE:FREQ=HOURLY;INTERVAL=1")

        with self.current_user(org_admin.username, user_password):
            # test create
            schedule_pg = schedules_pg.post(payload)
            # test get
            schedule_pg.get()
            # test put/patch
            schedule_pg.put()
            schedule_pg.patch()
            # test delete
            schedule_pg.delete()

    def test_system_job_template_schedule_crud_as_org_admin(self, request, org_admin, user_password, cleanup_jobs_template):
        """Tests schedules CRUD as an org_admin against a system job template."""
        schedules_pg = cleanup_jobs_template.get_related('schedules')
        # Tower-3.0 comes with a prestocked cleanup_jobs schedule
        schedule_pg = cleanup_jobs_template.get_related('schedules').results[0]

        with self.current_user(org_admin.username, user_password):
            # test get
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.get()
            # test put/patch
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.patch()
            # test post
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedules_pg.post()
            # test delete
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.delete()

    def test_crud_as_org_user(self, request, org_user, user_password, resource_with_schedule):
        """Test schedules CRUD as an org_user against an inventory_source, project, and JT."""
        schedules_pg = resource_with_schedule.get_related('schedules')
        schedule_pg = resource_with_schedule.get_related('schedules').results[0]

        with self.current_user(org_user.username, user_password):
            # test get
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.get()
            # test put/patch
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.patch()
            # test create
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedules_pg.post()
            # test delete
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.delete()

    def test_user_capabilities_as_superuser(self, resource_with_schedule, api_schedules_pg):
        """Tests 'user_capabilities' against schedules of all types of UJT
        as superuser."""
        schedule_pg = resource_with_schedule.get_related('schedules').results[0]
        check_user_capabilities(schedule_pg.get(), 'superuser')
        check_user_capabilities(api_schedules_pg.get(id=schedule_pg.id).results.pop().get(), "superuser")

    def test_user_capabilities_as_org_admin(self, org_admin, user_password, organization_resource_with_schedule, api_schedules_pg):
        """Tests 'user_capabilities' against schedules of all types of UJT
        as an org_admin."""
        schedule_pg = organization_resource_with_schedule.get_related('schedules').results[0]

        with self.current_user(org_admin.username, user_password):
            check_user_capabilities(schedule_pg.get(), 'org_admin')
            check_user_capabilities(api_schedules_pg.get(id=schedule_pg.id).results.pop().get(), "org_admin")


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_License_RBAC(Base_Api_Test):

    def test_delete_as_non_superuser(self, non_superuser, user_password, auth_user, api_config_pg):
        """Verify that DELETE to /api/v1/config/ as a non-superuser raises a 403.
        """
        with auth_user(non_superuser), pytest.raises(towerkit.exceptions.Forbidden):
            api_config_pg.delete()

    def test_post_as_non_superuser(self, non_superuser, user_password, auth_user, api_config_pg):
        """Verify that DELETE to /api/v1/config/ as a non-superuser raises a 403.
        """
        with auth_user(non_superuser), pytest.raises(towerkit.exceptions.Forbidden):
            api_config_pg.post()
