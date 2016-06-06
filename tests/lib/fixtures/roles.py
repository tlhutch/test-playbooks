from contextlib import contextmanager

import pytest

from common.api.pages import Role_Page
from common.api.pages import Roles_Page
from common.exceptions import NoContent_Exception


@pytest.fixture
def auth_user(testsetup, api_authtoken_url):
    """Inject a context manager for user authtoken switching on api models.
    The context manager is a wrapped function which takes a user api model
    and optional password.
    """
    @contextmanager
    def _auth_user(user, password='fo0m4nchU'):
        """Switch authorization context to that of a user corresponding to
        the api model of a user details endpoint.

        Args:
            user (Base): An api page model for a user
            password (optional[str]): The password of the user

        Example:
            Verify that patching a job_template as a user with insufficient
            permissions raises a Forbidden Content Exception

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
def get_role_pages(request):
    """Inject a role page generator as a pytest fixture. The generator is a
    wrapped function which takes an api page object as its argument and yields
    a role page model for each available role on the related roles endpoint
    associated with the page model.
    """
    def _get_role_pages(model):
        """Generates role page objects for a given api page model.

        Args:
            model (Base): An api page model with a related roles endpoint

        Yields:
            Role_Page: A role page object from the related roles endpoint

        Example:
            Get the name and role id of each available role for a factory
            generated job template

            >>> foo_job_template = factories.job_template(name='foo')
            >>> roles = list(get_role_pages(foo_job_template))
            >>> [(r.name, r.id) for r in roles]
            [(571, u'Admin'), (572, u'Read'), (573, u'Execute')]
        """
        testsetup = request.getfuncargvalue('testsetup')
        url = model.get().json.related.object_roles
        roles_page = Roles_Page(testsetup, base_url=url)
        for role in roles_page.get().json.results:
            role_page = Role_Page(testsetup, base_url=role.url)
            yield role_page.get()
    return _get_role_pages


@pytest.fixture
def get_role_page(get_role_pages):
    """Inject a role lookup function as a pytest fixture. The function takes
    an api page object and role name as its arguments and returns a role page
    model associated with the provided role name.
    """
    def _get_role_page(model, role_name):
        """Return a role page model for an api page model and role name.

        Args:
            model (Base): An api page model with related roles endpoint
            role_name (str): The (case insensitive) name of the role

        Returns:
            Role_Page: A role page object from the related roles endpoint

        Raises:
            ValueError: If no role is found for the given role_name

        Example:
            Get the description of the Use role for a factory generated
            inventory

            >>> bar_inventory = factories.inventory(name='bar_test')
            >>> role_page = get_role_page(bar_inventory, 'Use')
            >>> role_page.description
            u'Can use the inventory in a job template'
        """
        search_name = role_name.lower()
        for role_page in get_role_pages(model):
            if role_page.name.lower() == search_name:
                return role_page
        msg = "Role '{0}' not found for {1}"
        msg = msg.format(role_name, type(model))
        raise ValueError(msg)
    return _get_role_page


@pytest.fixture
def add_roles(auth_user, get_role_page):
    """Inject a role lookup and add function as a pytest fixture. The function
    accepts a details endpoint api page object for a user and resource as well
    as a list of role names as arguments and associates the roles to the user.
    """
    def _add_roles(user, model, role_names):
        """Associate a list of roles to a user for a given api page model

        Args:
            user (Base): An api page model for a user
            model (Base): An api page model with related roles endpoint
            role_names (list): a (case insensitive) list of role names

        Example:
            Make a user that is an organization admin with 'Use' and 'Update'
            on a test inventory

            >>> foo_organization = factories.organization(name='foo')
            >>> bar_inventory = factories.inventory(name='bar')
            >>> test_user = factories.user()
            >>> add_roles(test_user, foo_organization, ['admin'])
            >>> add_roles(test_user, bar_inventory, ['use', 'update'])
        """
        role_pages = [get_role_page(model, n) for n in role_names]
        for rp in role_pages:
            with pytest.raises(NoContent_Exception):
                rp.get_related('users').post({'id': user.id})
    return _add_roles
