import pytest
from contextlib import contextmanager

import towerkit.exceptions
from towerkit.api.pages import Role_Page, Roles_Page, Team_Page, User_Page


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
        token = testsetup.api.post(api_authtoken_url, data).json()['token']

        try:
            testsetup.api.login(token=token)
            yield
        finally:
            testsetup.api.session.auth = prev_auth
    return _auth_user


@pytest.fixture(scope='session')
def get_role():
    def _get_role(model, role_name):
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
        url = model.get().json.related.object_roles
        for obj_role in Roles_Page(model.testsetup, base_url=url).get().json.results:
            role = Role_Page(model.testsetup, base_url=obj_role.url).get()
            if role.name.lower() == search_name:
                return role

        msg = "Role '{0}' not found for {1}".format(role_name, type(model))
        raise ValueError(msg)
    return _get_role


@pytest.fixture(scope='session')
def set_roles(get_role):
    def _set_roles(agent, model, role_names, endpoint='related_users', disassociate=False):
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
    return _set_roles


@pytest.fixture
def set_test_roles(factories, set_roles):
    """Helper fixture used in creating the roles used in our RBAC tests."""
    def func(user_pg, tower_object, agent, role):
        """:param user_pg: The api page model for a user
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
    """Iterates through the Tower objects that support notifications."""
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function", params=['organization', 'job_template', 'custom_inventory_source', 'project'])
def resource_with_notification(request, email_notification_template):
    """Tower resource with an associated email notification template."""
    resource = request.getfuncargvalue(request.param)

    # associate our email NT with all notification template endpoints
    payload = dict(id=email_notification_template.id)
    endpoints = ['notification_templates_any', 'notification_templates_success', 'notification_templates_error']
    for endpoint in endpoints:
        with pytest.raises(towerkit.exceptions.NoContent):
            resource.get_related(endpoint).post(payload)
    return resource
