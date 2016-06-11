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