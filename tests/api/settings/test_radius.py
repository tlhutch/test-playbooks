from towerkit import exceptions as exc
from towerkit import config, utils
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.mp_group('RADIUS', 'isolated_serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited', 'skip_if_fips_enabled')
class TestRADIUS(APITest):

    username = config.credentials.radius.username
    password = config.credentials.radius.password

    @pytest.fixture
    def enable_radius_auth(self, request, api_settings_radius_pg):
        def func():
            radius_config = config.credentials.radius
            payload = {'RADIUS_SERVER': radius_config.server,
                       'RADIUS_PORT': radius_config.port,
                       'RADIUS_SECRET': radius_config.secret}
            api_settings_radius_pg.patch(**payload)
            request.addfinalizer(api_settings_radius_pg.delete)
            utils.logged_sleep(1)  # give auth settings time to take effect
        return func

    def test_authenticate_with_valid_credentials(self, request, v2, enable_radius_auth):
        assert v2.users.get(username=self.username).count == 0
        enable_radius_auth()

        with self.current_user(username=self.username, password=self.password):
            user = v2.me.get().results.pop()
        request.addfinalizer(user.delete)

        assert user.username == self.username
        assert user.external_account == 'enterprise'
        assert user.is_superuser is False
        assert user.is_system_auditor is False
        assert user.auth == []
        assert v2.users.get(username=self.username).count == 1

    def test_authentication_attempt_with_invalid_credentials_rejected(self, v2, enable_radius_auth):
        assert v2.users.get(username=self.username).count == 0
        enable_radius_auth()

        with self.current_user(username=self.username, password='invalid_password'):
            with pytest.raises(exc.Unauthorized):
                v2.me.get()
        assert v2.users.get(username=self.username).count == 0

    def test_radius_users_cannot_change_password(self, request, v2, enable_radius_auth):
        assert v2.users.get(username=self.username).count == 0
        enable_radius_auth()

        with self.current_user(username=self.username, password=self.password):
            user = v2.me.get().results.pop()
        request.addfinalizer(user.delete)

        user.patch(password='fake', password_confirm='fake')

        with self.current_user(username=self.username, password=self.password):
            v2.me.get()
        with self.current_user(username=self.username, password='fake'):
            with pytest.raises(exc.Unauthorized):
                v2.me.get()
