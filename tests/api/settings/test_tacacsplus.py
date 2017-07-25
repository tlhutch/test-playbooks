import logging
from datetime import datetime

import pytest

from tests.api import Base_Api_Test
from towerkit import exceptions as exc
from towerkit.config import config

log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def enable_tacacs_auth(request, v1, api_settings_tacacsplus_pg):
    def _enable_tacacs_auth(protocol='ascii'):
        tacacs_config = config.credentials.tacacs_plus
        payload = {'TACACSPLUS_HOST': tacacs_config.host,
                   'TACACSPLUS_PORT': tacacs_config.port,
                   'TACACSPLUS_SECRET': tacacs_config.secret,
                   'TACACSPLUS_SESSION_TIMEOUT': 5,
                   'TACACSPLUS_AUTH_PROTOCOL': protocol}
        api_settings_tacacsplus_pg.put(payload)
        request.addfinalizer(api_settings_tacacsplus_pg.delete)
    return _enable_tacacs_auth


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_TACACS_Plus(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_login_as_new_user(self, protocol, enable_tacacs_auth, v1, api_me_pg):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        assert not v1.users.get(username=tacacs_config.user).count

        with self.current_user(tacacs_config.user, getattr(tacacs_config, protocol + '_pass')):
            api_me_pg.get()

        users = v1.users.get(username=tacacs_config.user).results
        assert len(users) == 1, \
            "User {0} should be created after authenticating with TACACS+ server".format(tacacs_config.user)
        users.pop().delete()

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_repeated_login_with_tacacs_auth(self, protocol, enable_tacacs_auth, v1):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        username, password = (tacacs_config.user, getattr(tacacs_config, protocol + '_pass'))
        assert not v1.users.get(username=tacacs_config.user).count

        with self.current_user(username, password):
            user = v1.me.get().results.pop()
            assert user.username == username
            user_id = user.id
            user.first_name = 'changed'
            v1.authtoken.delete()

        with self.current_user(username, password):
            assert user_id == v1.me.get().results.pop().id, "Found different user_id on second login"
            assert user.get().first_name == 'changed', \
                'Change to user (first_name) did not persist across logins'
        user.delete()

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/6169')
    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_login_as_existing_user(self, protocol, enable_tacacs_auth, v1, api_me_pg):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        user = v1.users.create(username=tacacs_config.user)

        with self.current_user(tacacs_config.user, getattr(tacacs_config, protocol + '_pass')):
            with pytest.raises(exc.Unauthorized):
                api_me_pg.get()
        user.delete()

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_login_as_fake_user(self, protocol, enable_tacacs_auth, v1, api_me_pg):
        enable_tacacs_auth(protocol)
        with self.current_user('fake_user', 'fake_pass'):
            with pytest.raises(exc.Unauthorized):
                api_me_pg.get()

    def test_timeout(self, enable_tacacs_auth, v1, api_me_pg, api_settings_tacacsplus_pg):
        enable_tacacs_auth()
        api_settings_tacacsplus_pg.patch(TACACSPLUS_HOST='169.254.1.0', TACACSPLUS_SESSION_TIMEOUT=20)
        user = v1.users.create()

        start = datetime.now()
        # Tower should first attempt to authenticate using TACACS+ server, then use local login
        with self.current_user(user.username, user.password):
            api_me_pg.get()
        end = datetime.now()

        assert (end - start).total_seconds() - 20 < 5
        user.delete()

    @pytest.mark.parametrize('protocol', ['ascii', 'pap'])
    def test_tacacs_account_should_not_grant_access_to_existing_account(self, protocol, enable_tacacs_auth, v1, factories):
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
    def test_cannot_change_password_for_tacacs_user_in_tower(self, v1, enable_tacacs_auth, api_me_pg, protocol):
        enable_tacacs_auth(protocol)
        tacacs_config = config.credentials.tacacs_plus
        username, password = (tacacs_config.user, getattr(tacacs_config, protocol + '_pass'))
        assert not v1.users.get(username=username).count

        with self.current_user(username, password):
            user = v1.users.get(username=username).results.pop()
            user.patch(password='shouldntw0rk')

        with pytest.raises(exc.Unauthorized):
            with self.current_user(username, 'shouldntw0rk'):
                api_me_pg.get()

        with self.current_user(username, password):
            api_me_pg.get()

        user.delete()
