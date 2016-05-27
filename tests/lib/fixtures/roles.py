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
def get_role_pages(request):
    def _get_role_pages(model):
        testsetup = request.getfuncargvalue('testsetup')
        url = model.get().json.related.roles
        roles_page = Roles_Page(testsetup, base_url=url)
        for role in roles_page.get().json.results:
            role_page = Role_Page(testsetup, base_url=role.url)
            yield (role.name, role_page.get())
    return _get_role_pages


@pytest.fixture
def get_role_page(get_role_pages):
    def _get_role_page(model, role_name):
        search_name = role_name.lower()
        for name, role_page in get_role_pages(model):
            if name.lower() == search_name:
                return role_page
        msg = "Role '{0}' not found for {1}"
        msg = msg.format(role_name, type(model))
        raise ValueError(msg)
    return _get_role_page


@pytest.fixture
def add_roles(auth_user, get_role_page):
    def _add_roles(user, model, role_names):
        role_pages = [get_role_page(model, n) for n in role_names]
        for rp in role_pages:
            with pytest.raises(NoContent_Exception):
                rp.get_related('users').post({'id': user.id})
    return _add_roles
