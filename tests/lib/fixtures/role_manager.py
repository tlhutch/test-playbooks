from contextlib import contextmanager

import pytest

class RoleContextManager(object):
    def __init__(self, api, auth_url, username, add_role_function):
        self.api = api
        self.auth_url = auth_url
        self.username = username
        self._add_role_function = add_role_function  # XX

    def request_authtoken(self, password):
        data = {'username': self.username, 'password': password}
        response = self.api.post(self.auth_url, data)
        return response.json()['token']

    def add_role(self, model, role_name):
        self._add_role_function(model, role_name, self.username)

    def add_role_spec(self, role_spec):
        for model, role_names in role_spec.iteritems():
            # associate roles to the test user
            for role_name in role_names:
                self.add_role(model, role_name)

    @contextmanager
    def auth_user(self, password='fo0m4nchU'):
        try:
            intial_authtoken = self.api.session.auth
            self.api.login(token=self.request_authtoken(password))
            yield
        finally:
            self.api.session.auth = intial_authtoken

@pytest.fixture(scope='function')
def role_manager(request, authtoken, user_factory, add_role):
    # extract api fixture dependencies from requesting context
    api = request.getfuncargvalue('testsetup').api
    url = request.getfuncargvalue('api_authtoken_url')
    # create test user
    user = user_factory()
    rcm = RoleContextManager(api, url, user.username, add_role)
    return rcm


@pytest.fixture(scope='function')
def param_role_manager(request, role_manager):
    """Return a role context manager preloaded with a test user associated
    with roles from an indirect fixture-parametrized role_spec
    """
    # create and populate a role spec
    role_spec = {}
    for fixture_name, role_names in request.param.iteritems():
        # get the model fixture by name using the requesting context
        model = request.getfuncargvalue(fixture_name)
        role_spec[model] = role_names
    # associate roles to the test user
    role_manager.add_role_spec(role_spec)
    return role_manager


##############################################################################

from common.api.pages import Role_Page, Roles_Page  # NOQA
from common.exceptions import NoContent_Exception  # NOQA

# XX - This fixture is temporary and represents role lookup + add capabilities
# not yet implemented in the page models. I'll solve this problem last.
@pytest.fixture
def add_role(request, user_factory):
    def _add_role(model, role_name, user):
        if isinstance(user, str) or isinstance(user, unicode):
            user = user_factory(username=user)
        testsetup = request.getfuncargvalue('testsetup')
        role_name = role_name.lower()
        roles_url = model.get().json.related.roles
        results = Roles_Page(testsetup, base_url=roles_url).get().json.results
        try:
            role = next(r for r in results if r.name.lower() == role_name)
        except StopIteration:
            msg = "Role '{0}' not found for {1}"
            raise ValueError(msg.format(role_name, type(model)))
        role_page = Role_Page(testsetup, base_url=role.url)
        with pytest.raises(NoContent_Exception):
            role_page.get().get_related('users').post({'id': user.get().id})
    return _add_role
