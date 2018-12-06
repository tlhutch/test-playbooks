from datetime import datetime

from towerkit import exceptions as exc
from towerkit.config import config
from towerkit import utils
import pytest

from tests.api import APITest


@pytest.fixture(scope="function")
def enable_tacacs_auth(update_setting_pg, api_settings_tacacsplus_pg):
    def _enable_tacacs_auth(protocol='ascii'):
        tacacs_config = config.credentials.tacacs_plus
        payload = {'TACACSPLUS_HOST': tacacs_config.host,
                   'TACACSPLUS_PORT': tacacs_config.port,
                   'TACACSPLUS_SECRET': tacacs_config.secret,
                   'TACACSPLUS_SESSION_TIMEOUT': 5,
                   'TACACSPLUS_AUTH_PROTOCOL': protocol}
        update_setting_pg(api_settings_tacacsplus_pg, payload)
        utils.logged_sleep(1)  # Give auth settings time to take effect
    return _enable_tacacs_auth


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.mp_group('TACACSPlus', 'isolated_serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited', 'skip_if_fips_enabled')
class TestTACACSPlus(APITest):

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_login_as_new_user(self, request, protocol, enable_tacacs_auth, v1, api_me_pg):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        assert not v1.users.get(username=tacacs_config.user).count

        with self.current_user(tacacs_config.user, getattr(tacacs_config, protocol + '_pass')):
            tacacs_user = api_me_pg.get().results.pop()
            request.addfinalizer(tacacs_user.silent_delete)

        users = v1.users.get(username=tacacs_config.user).results
        assert len(users) == 1, \
            "User {0} should be created after authenticating with TACACS+ server".format(tacacs_config.user)

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_repeated_login_with_tacacs_auth(self, request, protocol, enable_tacacs_auth, v1):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        username, password = (tacacs_config.user, getattr(tacacs_config, protocol + '_pass'))
        assert not v1.users.get(username=tacacs_config.user).count

        with self.current_user(username, password):
            user = v1.me.get().results.pop()
            request.addfinalizer(user.silent_delete)
            assert user.username == username
            user_id = user.id
            user.first_name = 'changed'
            v1.connection.logout()

        with self.current_user(username, password):
            assert user_id == v1.me.get().results.pop().id, "Found different user_id on second login"
            assert user.get().first_name == 'changed', \
                'Change to user (first_name) did not persist across logins'

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_login_as_existing_user(self, factories, protocol, enable_tacacs_auth, api_me_pg):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        factories.v2_user(username=tacacs_config.user)

        with self.current_user(tacacs_config.user, getattr(tacacs_config, protocol + '_pass')):
            with pytest.raises(exc.Unauthorized):
                api_me_pg.get()

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_login_as_fake_user(self, protocol, enable_tacacs_auth, v1, api_me_pg):
        enable_tacacs_auth(protocol)
        with self.current_user('fake_user', 'fake_pass'):
            with pytest.raises(exc.Unauthorized):
                api_me_pg.get()

    def test_timeout(self, factories, enable_tacacs_auth, api_me_pg, api_settings_tacacsplus_pg):
        enable_tacacs_auth()
        api_settings_tacacsplus_pg.patch(TACACSPLUS_HOST='169.254.1.0', TACACSPLUS_SESSION_TIMEOUT=20)
        user = factories.v2_user()

        start = datetime.now()
        # Tower should first attempt to authenticate using TACACS+ server, then use local login
        with self.current_user(user.username, user.password):
            api_me_pg.get()
        end = datetime.now()

        assert (end - start).total_seconds() - 20 < 5

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_tacacs_account_should_not_grant_access_to_existing_account(self, factories, v1, protocol,
                                                                        enable_tacacs_auth):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        username, password = (tacacs_config.user, getattr(tacacs_config, protocol + '_pass'))
        assert not v1.users.get(username=username).count

        factories.user(username=username, password='p4ssword', is_superuser=True)
        with self.current_user(username, 'p4ssword'):
            v1.users.get()

        with pytest.raises(exc.Unauthorized):
            with self.current_user(username, password):
                v1.users.get()

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_cannot_change_password_for_tacacs_user_in_tower(self, request, v1, enable_tacacs_auth, protocol):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        username, password = (tacacs_config.user, getattr(tacacs_config, protocol + '_pass'))
        assert not v1.users.get(username=username).count

        with self.current_user(username, password):
            user = v1.users.get(username=username).results.pop()
            request.addfinalizer(user.silent_delete)
            user.patch(password='shouldntw0rk')

        with pytest.raises(exc.Unauthorized):
            with self.current_user(username, 'shouldntw0rk'):
                v1.me.get()

        with self.current_user(username, password):
            v1.me.get()

    def test_confirm_tacacs_host_and_secret_required(self, update_setting_pg, api_settings_tacacsplus_pg):
        with pytest.raises(exc.BadRequest) as e:
            update_setting_pg(api_settings_tacacsplus_pg, dict(TACACSPLUS_HOST='127.0.0.1'))
        assert e.value.msg == {'__all__': ['TACACSPLUS_SECRET is required when TACACSPLUS_HOST is provided.']}
