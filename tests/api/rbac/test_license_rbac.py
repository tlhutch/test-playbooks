import pytest

import towerkit.exceptions
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_License_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken')

    def test_delete_as_non_superuser(self, non_superuser, user_password, auth_user, api_config_pg):
        """Verify that DELETE to /api/v1/config/ as a non-superuser raises a 403."""
        with auth_user(non_superuser), pytest.raises(towerkit.exceptions.Forbidden):
            api_config_pg.delete()

    def test_post_as_non_superuser(self, non_superuser, user_password, auth_user, api_config_pg):
        """Verify that DELETE to /api/v1/config/ as a non-superuser raises a 403."""
        with auth_user(non_superuser), pytest.raises(towerkit.exceptions.Forbidden):
            api_config_pg.post()
