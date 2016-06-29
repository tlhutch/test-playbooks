from contextlib import contextmanager
import httplib
import logging

import pytest

import common.exceptions
from common.exceptions import Forbidden_Exception
from common.exceptions import NoContent_Exception
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


def set_roles(user, model, role_names, endpoint='related_users', disassociate=False):
    """Associate a list of roles to a user for a given api page model

    :param user: The api page model for a user
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
            payload = {'id': user.id}
            endpoint_model = role.get_related('users')
        elif endpoint == 'related_roles':
            payload = {'id': role.id}
            endpoint_model = user.get_related('roles')
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
    'resource_name,initial_role,unauthorized_target_role',
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
            with pytest.raises(common.exceptions.NotFound_Exception):
                organization_pg.get()
            for related in organization_pg.json.related:
                with pytest.raises(common.exceptions.NotFound_Exception):
                    organization_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.NotFound_Exception):
                organization_pg.put()
            with pytest.raises(common.exceptions.NotFound_Exception):
                organization_pg.patch()
            with pytest.raises(common.exceptions.NotFound_Exception):
                organization_pg.delete()

    def test_auditor_role(self, factories, user_password):
        '''
        An organization auditor should be able to do the following:
        * Issue GETs to our organization details page
        * Issue GETs to all of this organization's related pages

        An organization auditor should not be able to do the following:
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user auditor privileges
        role_pg = organization_pg.get_object_role('auditor_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            organization_pg.get()
            for related in organization_pg.json.related:
                organization_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.delete()

    def test_admin_role(self, factories, user_password):
        '''
        An organization admin should be able to do the following:
        * GET our organization details page
        * GET all of our organization's related pages
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user admin privileges
        role_pg = organization_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            organization_pg.get()
            for related in organization_pg.json.related:
                organization_pg.get_related(related)

            # check put/patch/delete
            organization_pg.put()
            organization_pg.patch()
            organization_pg.delete()

    def test_member_role(self, factories, user_password):
        '''
        Tests that a user with 'member_role' has the following:
        * The ability to make a GET to our target organization
        * The ability to make a GET against our organization's related endpoints

        Our user, however, should not be able to:
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user member privileges
        role_pg = organization_pg.get_object_role('member_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            organization_pg.get()
            for related in organization_pg.json.related:
                organization_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.delete()

    def test_read_role(self, factories, user_password):
        '''
        Tests that a user with 'read_role' has the following:
        * The ability to make a GET to our target organization
        * The ability to make a GET against our organization's related endpoints

        Our user, however, should not be able to:
        * Edit our organization
        * Delete our organization
        '''
        organization_pg = factories.organization()
        user_pg = factories.user()

        # give test user read role privileges
        role_pg = organization_pg.get_object_role('read_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            organization_pg.get()
            for related in organization_pg.json.related:
                organization_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                organization_pg.delete()

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
        role_pg = organization_pg.get_object_role('member_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

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


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Project_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user should not be able to:
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
            with pytest.raises(common.exceptions.NotFound_Exception):
                project_pg.get()
            for related in project_pg.json.related:
                with pytest.raises(common.exceptions.NotFound_Exception):
                    project_pg.get_related(related)

            # check project update
            with pytest.raises(common.exceptions.NotFound_Exception):
                update_pg.post()

            # check put/patch/delete
            with pytest.raises(common.exceptions.NotFound_Exception):
                project_pg.put()
            with pytest.raises(common.exceptions.NotFound_Exception):
                project_pg.patch()
            with pytest.raises(common.exceptions.NotFound_Exception):
                project_pg.delete()

    def test_admin_role(self, factories, user_password):
        '''
        A project admin should be able to:
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

        # give user admin_role
        role_pg = project_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            project_pg.get()
            for related in project_pg.json.related:
                # 403 when navigating to projects/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        project_pg.get_related(related)
                else:
                    project_pg.get_related(related)

            # check project update
            project_pg.update()

            # check put/patch/delete
            project_pg.put()
            project_pg.patch()
            project_pg.delete()

    def test_update_role(self, factories, user_password):
        '''
        A user with project update should be able to:
        * GET our project detail page
        * GET all project related pages
        * Launch project updates

        A user with project update should not be able to:
        * Use our project in a JT
        * Edit our project
        * Delete our project

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give user update_role
        role_pg = project_pg.get_object_role('update_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            project_pg.get()
            for related in project_pg.json.related:
                # 403 when navigating to projects/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        project_pg.get_related(related)
                else:
                    project_pg.get_related(related)

            # check project update
            project_pg.update()

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.delete()

    def test_use_role(self, factories, user_password):
        '''
        A user with project update should be able to:
        * GET our project detail page
        * GET all project related pages
        * Use our project in a JT

        A user with project update should not be able to:
        * Launch project updates
        * Edit our project
        * Delete our project

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give user use_role
        role_pg = project_pg.get_object_role('use_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            project_pg.get()
            for related in project_pg.json.related:
                # 403 when navigating to projects/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        project_pg.get_related(related)
                else:
                    project_pg.get_related(related)

            # check project update
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.update()

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.delete()

    def test_read_role(self, factories, user_password):
        '''
        A user with project read should be able to:
        * GET our project detail page
        * GET all project related pages

        A user with project read should not be able to:
        * Launch project updates
        * Use our project in a JT
        * Edit our project
        * Delete our project

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        project_pg = factories.project()
        user_pg = factories.user()

        # give user read_role
        role_pg = project_pg.get_object_role('read_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            project_pg.get()
            for related in project_pg.json.related:
                # 403 when navigating to projects/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        project_pg.get_related(related)
                else:
                    project_pg.get_related(related)

            # check project update
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.update()

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                project_pg.delete()


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Credential_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user should not be able to:
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
            with pytest.raises(common.exceptions.NotFound_Exception):
                credential_pg.get()
            for related in credential_pg.json.related:
                with pytest.raises(common.exceptions.NotFound_Exception):
                    credential_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.NotFound_Exception):
                credential_pg.put()
            with pytest.raises(common.exceptions.NotFound_Exception):
                credential_pg.patch()
            with pytest.raises(common.exceptions.NotFound_Exception):
                credential_pg.delete()

    def test_admin_role(self, factories, user_password):
        '''
        A user with credential 'owner' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        # Use this credential in creating a JT
        * Edit the credential
        * Delete the credential

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        credential_pg = factories.credential()
        user_pg = factories.user()

        # give user admin_role
        role_pg = credential_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            credential_pg.get()
            for related in credential_pg.json.related:
                credential_pg.get_related(related)

            # check put/patch/delete
            credential_pg.put()
            credential_pg.patch()
            credential_pg.delete()

    def test_use_role(self, factories, user_password):
        '''
        A user with credential 'use' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        * Use this credential in creating a JT

        A user with credential 'use' should not be able to:
        * Edit the credential
        * Delete the credential

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        credential_pg = factories.credential()
        user_pg = factories.user()

        # give user use_role
        role_pg = credential_pg.get_object_role('use_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            credential_pg.get()
            for related in credential_pg.json.related:
                credential_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                credential_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                credential_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                credential_pg.delete()

    def test_read_role(self, factories, user_password):
        '''
        A user with credential 'read' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related

        A user with credential 'read' should not be able to:
        * Use this credential in creating a JT
        * Edit the credential
        * Delete the credential

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        credential_pg = factories.credential()
        user_pg = factories.user()

        # give user read_role
        role_pg = credential_pg.get_object_role('read_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            credential_pg.get()
            for related in credential_pg.json.related:
                credential_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                credential_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                credential_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                credential_pg.delete()


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Team_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged user may not be able to:
        * Get the team details page
        * Get all of the team related pages
        * Edit the team
        * Delete the team
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            with pytest.raises(common.exceptions.NotFound_Exception):
                team_pg.get()
            for related in team_pg.json.related:
                with pytest.raises(common.exceptions.NotFound_Exception):
                    team_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.NotFound_Exception):
                team_pg.put()
            with pytest.raises(common.exceptions.NotFound_Exception):
                team_pg.patch()
            with pytest.raises(common.exceptions.NotFound_Exception):
                team_pg.delete()

    def test_admin_role(self, factories, user_password):
        '''
        A user with team 'admin_role' should be able to:
        * Get the team details page
        * Get all of the team related pages
        * Edit the team
        * Delete the team
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        # give user admin_role
        role_pg = team_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            team_pg.get()
            for related in team_pg.json.related:
                # 403 when navigating to teams/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        team_pg.get_related(related)
                else:
                    team_pg.get_related(related)

            # check put/patch/delete
            team_pg.put()
            team_pg.patch()
            team_pg.delete()

    def test_member_role(self, factories, user_password):
        '''
        A user with team 'member_role' should be able to:
        * Get the team details page
        * Get all of the team related pages

        A user with team 'member_role' should not be able to:
        * Edit the team
        * Delete the team
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        # give user member_role
        role_pg = team_pg.get_object_role('member_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            team_pg.get()
            for related in team_pg.json.related:
                # 403 when navigating to teams/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        team_pg.get_related(related)
                else:
                    team_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                team_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                team_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                team_pg.delete()

    def test_read_role(self, factories, user_password):
        '''
        A user with team 'read_role' should be able to:
        * Get the team details page
        * Get all of the team related pages

        A user with team 'read_role' should not be able to:
        * Edit the team
        * Delete the team
        '''
        team_pg = factories.team()
        user_pg = factories.user()

        # give user read_role
        role_pg = team_pg.get_object_role('read_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            team_pg.get()
            for related in team_pg.json.related:
                # 403 when navigating to teams/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        team_pg.get_related(related)
                else:
                    team_pg.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                team_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                team_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                team_pg.delete()

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
        An unprivileged user may not be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related
        * Edit your inventory script
        * Delete your inventory script
        '''
        user_pg = factories.user()

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            with pytest.raises(common.exceptions.NotFound_Exception):
                inventory_script.get()
            for related in inventory_script.json.related:
                with pytest.raises(common.exceptions.NotFound_Exception):
                    inventory_script.get_related(related)

            # check put/patch/delete
            with pytest.raises(common.exceptions.NotFound_Exception):
                inventory_script.put()
            with pytest.raises(common.exceptions.NotFound_Exception):
                inventory_script.patch()
            with pytest.raises(common.exceptions.NotFound_Exception):
                inventory_script.delete()

    def test_admin_role(self, factories, inventory_script, user_password):
        '''
        A user with inventory_script 'admin' should be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related
        * Edit your inventory script
        * Delete your inventory script
        '''
        user_pg = factories.user()

        # assert value for 'script' present
        assert inventory_script.script
        script = inventory_script.script

        # give user admin_role
        role_pg = inventory_script.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            inventory_script.get()
            for related in inventory_script.json.related:
                # 403 when navigating to inventory_scripts/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        inventory_script.get_related(related)
                else:
                    inventory_script.get_related(related)

            # check that value of 'script' viewable
            assert inventory_script.script == script, \
                "Unexpected value for 'script'; expected %s but got %s." % (script, inventory_script.script)

            # check put/patch/delete
            inventory_script.put()
            inventory_script.patch()
            inventory_script.delete()

    def test_read_role(self, factories, inventory_script, user_password):
        '''
        A user with inventory_script 'read' should be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related

        A user with inventory_script 'read' should not be able to:
        * Edit your inventory script
        * Delete your inventory script
        '''
        user_pg = factories.user()

        # assert value for 'script' present
        assert inventory_script.script

        # give user read_role
        role_pg = inventory_script.get_object_role('read_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            inventory_script.get()
            for related in inventory_script.json.related:
                # 403 when navigating to inventory_scripts/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        inventory_script.get_related(related)
                else:
                    inventory_script.get_related(related)

            # check that value of 'script' not viewable
            assert not inventory_script.script, \
                "Unexpected value for 'script'; expected null but got %s." % inventory_script.script

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_script.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_script.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_script.delete()


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/2366')
    def test_unprivileged_user(self, factories, user_password):
        '''
        An unprivileged_user should not be able to:
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
            with pytest.raises(common.exceptions.NotFound_Exception):
                job_template_pg.get()
            for related in job_template_pg.json.related:
                with pytest.raises(common.exceptions.NotFound_Exception):
                    job_template_pg.get_related(related)

            # check JT launch
            with pytest.raises(common.exceptions.NotFound_Exception):
                launch_pg.post()

            # check put/patch/delete
            with pytest.raises(common.exceptions.NotFound_Exception):
                job_template_pg.put()
            with pytest.raises(common.exceptions.NotFound_Exception):
                job_template_pg.patch()
            with pytest.raises(common.exceptions.NotFound_Exception):
                job_template_pg.delete()

    def test_admin_role(self, factories, user_password):
        '''
        A user with JT admin should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Launch the JT
        * Edit the JT
        * Delete the JT
        '''
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give user admin_role
        role_pg = job_template_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            job_template_pg.get()
            for related in job_template_pg.json.related:
                # 403 when navigating to the following related is expected
                if related in ['credential', 'inventory', 'project']:
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        job_template_pg.get_related(related)
                else:
                    job_template_pg.get_related(related)

            # check JT launch
            job_pg = job_template_pg.launch().wait_until_completed()
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

            # check put/patch/delete
            job_template_pg.put()
            job_template_pg.patch()
            job_template_pg.delete()

    def test_execute_role(self, factories, user_password):
        '''
        A user with JT execute should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages
        * Launch the JT

        And should not be able to:
        * Edit the JT
        * Delete the JT
        '''
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give user execute_role
        role_pg = job_template_pg.get_object_role('execute_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            job_template_pg.get()
            for related in job_template_pg.json.related:
                # 403 when navigating to the following related is expected
                if related in ['credential', 'inventory', 'project']:
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        job_template_pg.get_related(related)
                else:
                    job_template_pg.get_related(related)

            # check JT launch
            job_pg = job_template_pg.launch().wait_until_completed()
            assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template_pg.delete()

    def test_read_role(self, factories, user_password):
        '''
        A user with JT admin should be able to:
        * Get the JT details page
        * Get all of the JT get_related pages

        And should not be able to:
        * Launch the JT
        * Edit the JT
        * Delete the JT
        '''
        job_template_pg = factories.job_template()
        user_pg = factories.user()

        # give user admin_role
        role_pg = job_template_pg.get_object_role('read_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            job_template_pg.get()
            for related in job_template_pg.json.related:
                # 403 when navigating to the following related is expected
                if related in ['credential', 'inventory', 'project']:
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        job_template_pg.get_related(related)
                else:
                    job_template_pg.get_related(related)

            # check JT launch
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template_pg.launch()

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                job_template_pg.delete()


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
        * Edit the inventory
        * Delete the inventory

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        user_pg = factories.user()

        command_pg = inventory_pg.get_related('ad_hoc_commands')
        inventory_source_pgs = [cloud_group.get_related('inventory_source') for cloud_group in cloud_groups]
        inventory_source_update_pgs = [inventory_source_pg.get_related('update') for inventory_source_pg in inventory_source_pgs]
        custom_group_update_pg = custom_group.get_related('inventory_source')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            with pytest.raises(common.exceptions.NotFound_Exception):
                inventory_pg.get()
            for related in inventory_pg.json.related:
                with pytest.raises(common.exceptions.NotFound_Exception):
                    inventory_pg.get_related(related)

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

            # check put/patch/delete
            with pytest.raises(common.exceptions.NotFound_Exception):
                inventory_pg.put()
            with pytest.raises(common.exceptions.NotFound_Exception):
                inventory_pg.patch()
            with pytest.raises(common.exceptions.NotFound_Exception):
                inventory_pg.delete()

    def test_admin_role(self, host_local, cloud_groups, custom_group, user_password, factories):
        '''
        A user with inventory admin should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Use the inventory in creating a JT
        * Edit the inventory
        * Delete the inventory

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        credential_pg = factories.credential()
        user_pg = factories.user()

        # give user inventory admin_role
        role_pg = inventory_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        # give user credential admin_role
        role_pg = credential_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            inventory_pg.get()
            for related in inventory_pg.json.related:
                # 403 when navigating to inventories/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        inventory_pg.get_related(related)
                else:
                    inventory_pg.get_related(related)

            # update all cloud_groups
            for cloud_group in cloud_groups:
                update_pg = custom_group.get_related('inventory_source').get_related('update')
                update_pg.post()

            # update custom group
            update_pg = custom_group.get_related('inventory_source').get_related('update')
            update_pg.post()

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping",
                           limit=host_local.name, )
            command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload).wait_until_completed()
            assert command_pg.is_successful, "Command unsuccessful - %s." % command_pg

            # check put/patch/delete
            inventory_pg.put()
            inventory_pg.patch()
            inventory_pg.delete()

    def test_use_role(self, host_local, custom_group, user_password, factories):
        '''
        A user with inventory use should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Use the inventory in creating a JT

        A user with inventory use should not be able to:
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Edit the inventory
        * Delete the inventory

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        credential_pg = factories.credential()
        user_pg = factories.user()

        # give user inventory use_role
        role_pg = inventory_pg.get_object_role('use_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        # give user credential admin_role
        role_pg = credential_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            inventory_pg.get()
            for related in inventory_pg.json.related:
                # 403 when navigating to inventories/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        inventory_pg.get_related(related)
                else:
                    inventory_pg.get_related(related)

            # update custom group
            update_pg = custom_group.get_related('inventory_source').get_related('update')
            with pytest.raises(common.exceptions.Forbidden_Exception):
                update_pg.post()

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping",
                           limit=host_local.name, )
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.get_related('ad_hoc_commands').post(payload)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.delete()

    def test_adhoc_role(self, host_local, custom_group, user_password, factories):
        '''
        A user with inventory adhoc should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Launch ad hoc commands against the inventory

        A user with inventory adhoc should not be able to:
        * Update all groups that the inventory contains
        * Use the inventory in creating a JT
        * Edit the inventory
        * Delete the inventory

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        credential_pg = factories.credential()
        user_pg = factories.user()

        # give user inventory adhoc
        role_pg = inventory_pg.get_object_role('adhoc_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        # give user credential admin_role
        role_pg = credential_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            inventory_pg.get()
            for related in inventory_pg.json.related:
                # 403 when navigating to inventories/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        inventory_pg.get_related(related)
                else:
                    inventory_pg.get_related(related)

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

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.delete()

    def test_update_role(self, host_local, cloud_groups, custom_group, user_password, factories):
        '''
        A user with inventory update should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Update all groups that the inventory contains

        A user with inventory update should not be able to:
        * Launch ad hoc commands against the inventory
        * Use the inventory in creating a JT
        * Edit the inventory
        * Delete the inventory

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        credential_pg = factories.credential()
        user_pg = factories.user()

        # give user inventory update_role
        role_pg = inventory_pg.get_object_role('update_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        # give user credential admin_role
        role_pg = credential_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            inventory_pg.get()
            for related in inventory_pg.json.related:
                # 403 when navigating to inventories/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        inventory_pg.get_related(related)
                else:
                    inventory_pg.get_related(related)

            # update all cloud_groups
            for cloud_group in cloud_groups:
                update_pg = custom_group.get_related('inventory_source').get_related('update')
                update_pg.post()

            # update custom group
            update_pg = custom_group.get_related('inventory_source').get_related('update')
            update_pg.post()

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping",
                           limit=host_local.name, )
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.get_related('ad_hoc_commands').post(payload)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.delete()

    def test_read_role(self, host_local, custom_group, user_password, factories):
        '''
        A user with inventory read should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related

        A user with inventory read should not be able to:
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Use the inventory in creating a JT
        * Edit the inventory
        * Delete the inventory

        Use tested already in test_usage_role_required_to_change_other_job_template_related_resources.
        '''
        inventory_pg = host_local.get_related('inventory')
        credential_pg = factories.credential()
        user_pg = factories.user()

        # give user inventory read_role
        role_pg = inventory_pg.get_object_role('read_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        # give user credential admin_role
        role_pg = credential_pg.get_object_role('admin_role')
        with pytest.raises(common.exceptions.NoContent_Exception):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            inventory_pg.get()
            for related in inventory_pg.json.related:
                # 403 when navigating to inventories/N/organization is expected
                if related == 'organization':
                    with pytest.raises(common.exceptions.Forbidden_Exception):
                        inventory_pg.get_related(related)
                else:
                    inventory_pg.get_related(related)

            # update custom group
            update_pg = custom_group.get_related('inventory_source').get_related('update')
            with pytest.raises(common.exceptions.Forbidden_Exception):
                update_pg.post()

            # post command
            payload = dict(inventory=inventory_pg.id,
                           credential=credential_pg.id,
                           module_name="ping",
                           limit=host_local.name, )
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.get_related('ad_hoc_commands').post(payload)

            # check put/patch/delete
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.put()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.patch()
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_pg.delete()
