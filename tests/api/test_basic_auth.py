from towerkit.api.client import Connection
from towerkit.ws import WSClient
from towerkit.config import config as qe_config
from towerkit import utils
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestBasicAuth(APITest):

    def test_basic_auth(self, factories):
        conn = Connection(qe_config.base_url)
        conn.session.auth = (
            qe_config.credentials.users.admin.username,
            qe_config.credentials.users.admin.password
        )
        resp = conn.get('/api/v2/me/')
        assert resp.json()['count'] == 1
        assert resp.status_code == 200
        assert 'sessionid' not in resp.headers.get('Set-Cookie', '')
        assert 'csrftoken' not in resp.headers.get('Set-Cookie', '')

    @pytest.mark.github('https://github.com/ansible/tower/issues/2339')
    def test_basic_auth_disabled(self, factories, v2, update_setting_pg):
        auth_settings = v2.settings.get().get_endpoint('authentication')
        update_setting_pg(auth_settings, {'AUTH_BASIC_ENABLED': False})

        conn = Connection(qe_config.base_url)
        conn.session.auth = (
            qe_config.credentials.users.admin.username,
            qe_config.credentials.users.admin.password
        )
        resp = conn.get('/api/v2/me/')
        assert resp.status_code == 401

        # Don't send back headers that will cause the browser to prompt for
        # basic auth credentials
        assert resp.headers['WWW-Authenticate'] == 'Bearer realm=api authorization_url=/api/o/authorize/'



    def spawn_session(self, user):
        session = Connection(self.connections['root'].server)
        session.get_session_requirements()
        resp = session.login(username=user.username, password=user.password, next='/')
        ws = WSClient(
              session_id=session.session_id,
              csrftoken=session.session.cookies.get('csrftoken')
              ).connect()
        reply = next(iter(ws))
        assert reply['user'] == user.id
        assert reply['accept'] is True
        ws.subscribe(control=['limit_reached_{}'.format(user.id)])
        return session, ws

    @pytest.mark.parametrize('max_logins', range(1, 4))
    def test_authtoken_maximum_concurrent_sessions(self, factories, v2, update_setting_pg, max_logins):
        total = 3
        update_setting_pg(v2.settings.get().get_endpoint(
            'authentication'), {'SESSIONS_PER_USER': max_logins})
        org = factories.v2_organization()
        user = factories.v2_user(organization=org)

        sessions = []
        ws_clients = []
        for _ in range(total):
             session, ws = self.spawn_session(user)
             sessions.append(session)
             ws_clients.append(ws)
             utils.logged_sleep(3)

        # every *invalid* Websocket client should get a logout notification
        invalid_logins = total - max_logins
        for ws in ws_clients[:invalid_logins]:
            reply = next(iter(ws))
        assert reply['group_name'] == 'control'
        assert reply['reason'] == 'limit_reached'

        responses = [s.get('/api/v2/me/').status_code for s in sessions]
        assert responses.count(200) == max_logins
        assert responses.count(401) == invalid_logins
