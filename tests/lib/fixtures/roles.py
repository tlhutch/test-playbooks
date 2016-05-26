from contextlib import contextmanager

import pytest

from common.api.pages import Role_Page
from common.api.pages import Roles_Page
from common.exceptions import NoContent_Exception

@pytest.fixture
def auth_user(testsetup, api_authtoken_url):
    """Inject a context manager for user authtoken switching on api models
    """
    @contextmanager
    def _auth_user(user, password='fo0m4nchU'):
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
def get_role_page(request):
    def _get_role_page(model, role_name):
        testsetup = request.getfuncargvalue('testsetup')
        role_name = role_name.lower()
        roles_url = model.get().json.related.roles
        results = Roles_Page(testsetup, base_url=roles_url).get().json.results
        try:
            role = next(r for r in results if r.name.lower() == role_name)
        except StopIteration:
            msg = "Role '{0}' not found for {1}"
            raise ValueError(msg.format(role_name, type(model)))
        return Role_Page(testsetup, base_url=role.url).get()
    return _get_role_page


@pytest.fixture(scope='function')
def add_roles(auth_user, get_role_page):
    def _add_roles(user, model, role_names):
        role_pages = [get_role_page(model, n) for n in role_names]
        for rp in role_pages:
            with pytest.raises(NoContent_Exception):
                rp.get_related('users').post({'id': user.id})
    return _add_roles
