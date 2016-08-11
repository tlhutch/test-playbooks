from contextlib import contextmanager
import httplib
import logging

import pytest

import common.exceptions
from common.exceptions import Forbidden_Exception
from common.exceptions import NoContent_Exception
from common.api.pages.users import User_Page
from common.api.pages.teams import Team_Page
from tests.api import Base_Api_Test

log = logging.getLogger(__name__)

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
            *** Forbidden_Exception
        """
        try:
            prev_auth = testsetup.api.session.auth
            data = {'username': user.username, 'password': password}
            response = testsetup.api.post(api_authtoken_url, data)
            testsetup.api.login(token=response.json()['token'])
            yield
        finally:
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
        """
        if agent == "user":
            set_roles(user_pg, tower_object, [role])
        elif agent == "team":
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
        with pytest.raises(NoContent_Exception):
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
        with pytest.raises(NoContent_Exception):
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
        httplib.NOT_FOUND: common.exceptions.NotFound_Exception,
        httplib.FORBIDDEN: common.exceptions.Forbidden_Exception,
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
        with pytest.raises(common.exceptions.NotFound_Exception):
            tower_object.get()
        for related in tower_object.related:
            with pytest.raises(common.exceptions.NotFound_Exception):
                tower_object.get_related(related)
    # for test scenarios involving privileged users
    else:
        tower_object.get()
        for related in tower_object.related:
            if related in expected_forbidden:
                with pytest.raises(common.exceptions.Forbidden_Exception):
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


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize('endpoint', ['related_users', 'related_roles'])
@pytest.mark.parametrize(
    'resource_name',
    ['organization', 'project', 'inventory', 'credential', 'job_template']
)
def test_role_association_and_disassociation(factories, resource_name, endpoint):
    """Verify basic role association and disassociation functionality
    """
    user = factories.user()
    resource = getattr(factories, resource_name)()
    for role in resource.object_roles:
        role_name = role.name
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
        ('project', 'read', 'admin'),
        ('inventory', 'read', 'admin'),
        ('job_template', 'read', 'admin'),
    ]
)
def test_unauthorized_self_privilege_escalation_returns_code_403(
        factories, auth_user, endpoint,
        resource_name, initial_role, unauthorized_target_role):
    """A user with [intial_role] permission on a [resource_name] cannot add
    the [unauthorized_target_role] for the [resource_name] to themselves
    """
    resource = getattr(factories, resource_name)()
    # make a test user and associate it with the initial role
    user = factories.user()
    set_roles(user, resource, [initial_role])
    with auth_user(user), pytest.raises(Forbidden_Exception):
        set_roles(user, resource, [unauthorized_target_role], endpoint=endpoint)


@pytest.mark.parametrize('payload_resource_roles,response_codes', [
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
    user = factories.user()
    data, resources = factories.job_template.payload()
    for name in ('credential', 'project', 'inventory'):
        set_roles(user, resources[name], ['use'])
    # make network credential and add it to payload
    network_credential = factories.credential(kind='net')
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

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
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
            assert_response_raised(organization_pg, httplib.NOT_FOUND)

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

        exc_info = pytest.raises(common.exceptions.BadRequest_Exception, team_pg.get_related('roles').post, payload)
        result = exc_info.value[1]
        assert result == {u'msg': u'You cannot assign an Organization role as a child role for a Team.'}, \
            "Unexpected error message received when attempting to assign an organization role to a team."


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Project_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user/team should not be able to:
        * GET our project detail page
        * GET all project related pages
        * Launch project updates
        * Use our project in a JT
        * Edit our project
        * Delete our project

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        project_pg = factories.project()
        user_pg = factories.user()
        update_pg = project_pg.get_related('update')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, unprivileged=True)

            # check project update
            with pytest.raises(common.exceptions.NotFound_Exception):
                update_pg.post()

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.NOT_FOUND)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with project 'admin' should be able to:
        * GET our project detail page
        * GET all project related pages
        * Launch project updates
        * Use our project in a JT
        * Edit our project
        * Delete our project

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, project_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check project update
            project_pg.update().wait_until_completed()

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with project 'update' should be able to:
        * GET our project detail page
        * GET all project related pages
        * Launch project updates

        A user/team with project 'update' should not be able to:
        * Use our project in a JT
        * Edit our project
        * Delete our project

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent update_role
        set_test_roles(user_pg, project_pg, agent, "update")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check project update
            project_pg.update()

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with project 'use' should be able to:
        * GET our project detail page
        * GET all project related pages
        * Use our project in a JT

        A user/team with project 'use' should not be able to:
        * Launch project updates
        * Edit our project
        * Delete our project

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent use_role
        set_test_roles(user_pg, project_pg, agent, "use")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check project update
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.update()

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with project 'read' should be able to:
        * GET our project detail page
        * GET all project related pages

        A user/team with project 'read' should not be able to:
        * Launch project updates
        * Use our project in a JT
        * Edit our project
        * Delete our project

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, project_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check project update
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.update()

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Credential_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user/team should not be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        # Use this credential in creating a JT
        * Edit the credential
        * Delete the credential

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        credential_pg = factories.credential()
        user_pg = factories.user()

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.NOT_FOUND)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with credential 'admin' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        # Use this credential in creating a JT
        * Edit the credential
        * Delete the credential

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
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
        * Use this credential in creating a JT

        A user/team with credential 'use' should not be able to:
        * Edit the credential
        * Delete the credential

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
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
        * Use this credential in creating a JT
        * Edit the credential
        * Delete the credential

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
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

    def test_autopopulated_admin_role_with_teams(self, factories):
        '''
        Tests that when you create a credential with a value supplied for 'team'
        that your team is automatically given the admin role of your credential.
        '''
        team_pg = factories.team()

        # assert newly created team has no roles
        assert not team_pg.get_related('roles').count, \
            "Newly created team created unexpectedly with roles - %s." % team_pg.get_related('roles')

        # assert team now has admin role after team credential creation
        credential_pg = factories.credential(team=team_pg, organization=None)
        admin_role_teams_pg = credential_pg.get_object_role('admin_role').get_related('teams')
        assert admin_role_teams_pg.count == 1, \
            "Unexpected number of teams with our credential admin role. Expected one, got %s." % admin_role_teams_pg.count
        assert admin_role_teams_pg.results[0].id == team_pg.id, \
            "Unexpected admin role team returned. Expected team with ID %s, but %s." % (team_pg.id, admin_role_teams_pg.results[0].id)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Team_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
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
            assert_response_raised(team_pg, httplib.NOT_FOUND)

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
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        # assert that teams/N/users now shows test user
        assert users_pg.get().count == 1, "Expected one user for teams/%s/users/, got %s." % (team_pg.id, users_pg.count)
        assert users_pg.results[0].id == user_pg.id, \
            "Team user not our target user. Expected user with ID %s but got one with ID %s." % (user_pg.id, users_pg.results[0].id)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory_Script_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
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
            assert_response_raised(inventory_script, httplib.NOT_FOUND)

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


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
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
            with pytest.raises(common.exceptions.NotFound_Exception):
                launch_pg.post()

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.NOT_FOUND)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with JT 'admin' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Launch the JT
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

            # check JT launch
            job_pg = job_template_pg.launch().wait_until_completed()
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

            # check put/patch/delete
            assert_response_raised(job_template_pg.get(), httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_execute_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with JT 'execute' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Launch the JT

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

            # check JT launch
            job_pg = job_template_pg.launch().wait_until_completed()
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        '''
        A user/team with JT 'admin' should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages

        A user/team with JT 'admin' should not be able to:
        * Launch the JT
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

            # check JT launch
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template_pg.launch()

            # check put/patch/delete
            assert_response_raised(job_template_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("role", ["admin", "execute", "read"])
    def test_job_template_can_edit(self, factories, user_password, role):
        '''
        Test that when users with JT 'admin' navigate to a JT details
        page that can_edit is True. can_edit should be False with
        all other users.
        '''
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['execute', 'read']

        user_pg = factories.user()
        job_template_pg = factories.job_template()

        # give user target role
        set_roles(user_pg, job_template_pg, [role])

        # check can_edit as our test user
        with self.current_user(username=user_pg.username, password=user_password):
            job_template_pg.get()
            if role in ALLOWED_ROLES:
                assert job_template_pg.summary_fields['can_edit'], \
                    "Expected JT can_edit to be True with a user with JT %s." % role
            elif role in REJECTED_ROLES:
                assert not job_template_pg.summary_fields['can_edit'], \
                    "Expected JT can_edit to be False with a user with JT %s." % role
            else:
                raise ValueError("Received unhandled JT role.")


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
    def test_unprivileged_user(self, host_local, cloud_groups, custom_group, user_password, factories):
        '''
        An unprivileged user should not be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Use the inventory in creating a JT
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        user_pg = factories.user()

        command_pg = inventory_pg.get_related('ad_hoc_commands')
        inventory_source_pgs = [cloud_group.get_related('inventory_source') for cloud_group in cloud_groups]
        inventory_source_update_pgs = [inventory_source_pg.get_related('update') for inventory_source_pg in inventory_source_pgs]
        custom_group_update_pg = custom_group.get_related('inventory_source')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, unprivileged=True)

            # update all cloud_groups
            for inventory_source_update_pg in inventory_source_update_pgs:
                with pytest.raises(common.exceptions.NotFound_Exception):
                    inventory_source_update_pg.post()

            # update custom group
            with pytest.raises(common.exceptions.NotFound_Exception):
                custom_group_update_pg.post()

            # post command
            with pytest.raises(common.exceptions.NotFound_Exception):
                command_pg.post()

            # check ability to create group and host
            with pytest.raises(common.exceptions.Forbidden_Exception):
                groups_pg.post()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                hosts_pg.post()

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.NOT_FOUND)
            assert_response_raised(custom_group, httplib.NOT_FOUND)
            assert_response_raised(inventory_pg, httplib.NOT_FOUND)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, host_local, cloud_groups, custom_group, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'admin' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Use the inventory in creating a JT
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give agent admin_role
        set_test_roles(user_pg, inventory_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # update all cloud_groups
            for cloud_group in cloud_groups:
                inventory_source_pg = cloud_group.get_related('inventory_source')
                inventory_source_pg.get_related('update').post()
                assert inventory_source_pg.wait_until_completed().is_successful, \
                    "Inventory update unsuccessful - %s." % inventory_source_pg

            # update custom group
            inventory_source_pg = custom_group.get_related('inventory_source')
            inventory_source_pg.get_related('update').post()
            assert inventory_source_pg.wait_until_completed().is_successful, \
                "Inventory update unsuccessful - %s." % inventory_source_pg

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping",
                           limit=host_local.name, )
            command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload).wait_until_completed()
            assert command_pg.is_successful, "Command unsuccessful - %s." % command_pg

            # check ability to create group and host
            groups_pg.post(group_payload)
            hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.OK)
            assert_response_raised(custom_group, httplib.OK)
            assert_response_raised(inventory_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, host_local, custom_group, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'use' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Use the inventory in creating a JT

        A user/team with inventory 'use' should not be able to:
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give agent use_role
        set_test_roles(user_pg, inventory_pg, agent, "use")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # update custom group
            update_pg = custom_group.get_related('inventory_source').get_related('update')
            with pytest.raises(common.exceptions.Forbidden_Exception):
                update_pg.post()

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping", )
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.get_related('ad_hoc_commands').post(payload)

            # check ability to create group and host
            with pytest.raises(common.exceptions.Forbidden_Exception):
                groups_pg.post(group_payload)
            with pytest.raises(common.exceptions.Forbidden_Exception):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(custom_group, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_adhoc_role(self, host_local, custom_group, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'adhoc' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Launch ad hoc commands against the inventory

        A user/team with inventory 'adhoc' should not be able to:
        * Update all groups that the inventory contains
        * Use the inventory in creating a JT
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give agent adhoc_role
        set_test_roles(user_pg, inventory_pg, agent, "ad hoc")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # update custom group
            update_pg = custom_group.get_related('inventory_source').get_related('update')
            with pytest.raises(common.exceptions.Forbidden_Exception):
                update_pg.post()

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping",
                           limit=host_local.name, )
            command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload).wait_until_completed()
            assert command_pg.is_successful, "Command unsuccessful - %s." % command_pg

            # check ability to create group and host
            with pytest.raises(common.exceptions.Forbidden_Exception):
                groups_pg.post(group_payload)
            with pytest.raises(common.exceptions.Forbidden_Exception):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(custom_group, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2710')
    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, host_local, cloud_groups, custom_group, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'update' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Update all groups that the inventory contains

        A user/team with inventory 'update' should not be able to:
        * Launch ad hoc commands against the inventory
        * Use the inventory in creating a JT
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give agent update_role
        set_test_roles(user_pg, inventory_pg, agent, "update")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # update all cloud_groups
            for cloud_group in cloud_groups:
                inventory_source_pg = cloud_group.get_related('inventory_source')
                inventory_source_pg.get_related('update').post()
                assert inventory_source_pg.wait_until_completed().is_successful, \
                    "Inventory update failed - %s." % inventory_source_pg

            # update custom group
            inventory_source_pg = custom_group.get_related('inventory_source')
            inventory_source_pg.get_related('update').post()
            assert inventory_source_pg.wait_until_completed(), \
                "Inventory update failed - %s." % inventory_source_pg

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping", )
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.get_related('ad_hoc_commands').post(payload)

            # check ability to create group and host
            with pytest.raises(common.exceptions.Forbidden_Exception):
                groups_pg.post(group_payload)
            with pytest.raises(common.exceptions.Forbidden_Exception):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(custom_group, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, host_local, custom_group, set_test_roles, agent, user_password, factories):
        '''
        A user/team with inventory 'read' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related

        A user/team with inventory 'read' should not be able to:
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Use the inventory in creating a JT
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give agent read_role
        set_test_roles(user_pg, inventory_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # update custom group
            update_pg = custom_group.get_related('inventory_source').get_related('update')
            with pytest.raises(common.exceptions.Forbidden_Exception):
                update_pg.post()

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping", )
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.get_related('ad_hoc_commands').post(payload)

            # check ability to create group and host
            with pytest.raises(common.exceptions.Forbidden_Exception):
                groups_pg.post(group_payload)
            with pytest.raises(common.exceptions.Forbidden_Exception):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(custom_group, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Notification_Template_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    def test_notification_template_create_as_unprivileged_user(self, email_notification_template_payload, api_notification_templates_pg,
                                                               unprivileged_user, user_password):
        '''
        Tests that unprivileged users may not create notification templates.
        '''
        # test notification template create as unprivileged user
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(common.exceptions.Forbidden_Exception):
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
                with pytest.raises(common.exceptions.Forbidden_Exception):
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
                with pytest.raises(common.exceptions.NoContent_Exception):
                    endpoint.post(payload)

    def test_notification_template_read_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        '''
        Tests that unprivileged users cannot read NT endpoints.
        '''
        # assert that we cannot access api/v1/notification_templates
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(common.exceptions.Forbidden_Exception):
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
            with pytest.raises(common.exceptions.Forbidden_Exception):
                email_notification_template.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
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
            with pytest.raises(common.exceptions.Forbidden_Exception):
                email_notification_template.delete()

    def test_notification_template_delete_as_org_admin(self, email_notification_template, org_admin, user_password):
        '''
        Tests that org_admins can delete NTs.
        '''
        # assert that delete is accepted
        with self.current_user(username=org_admin.username, password=user_password):
            email_notification_template.delete()


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Notifications_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    def test_notification_read_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        '''
        Test that unprivileged users cannot read notifications.
        '''
        notification_pg = email_notification_template.test().wait_until_completed()

        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(common.exceptions.Forbidden_Exception):
                notification_pg.get()

    def test_notification_read_as_org_admin(self, email_notification_template, org_admin, user_password):
        '''
        Test that org_admins can read notifications.
        '''
        notification_pg = email_notification_template.test().wait_until_completed()

        with self.current_user(username=org_admin.username, password=user_password):
            notification_pg.get()


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Label_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

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
            with pytest.raises(common.exceptions.Forbidden_Exception):
                api_labels_pg.post(payload)

        # grant user target organization permission
        set_roles(user_pg, organization_pg, [role])

        # assert label post accepted
        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                api_labels_pg.post(payload)
            elif role in REJECTED_ROLES:
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    api_labels_pg.post(payload)
            else:
                raise ValueError("Received unhandled organization role.")

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
            if job_template_pg.summary_fields['can_edit']:
                with pytest.raises(common.exceptions.NoContent_Exception):
                    labels_pg.post(payload)
            else:
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    labels_pg.post(payload)
