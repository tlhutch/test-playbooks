from towerkit.api.client import Connection
from towerkit.ws import WSClient
from towerkit.config import config as qe_config
from towerkit import utils
import pytest
import time

from tests.api import APITest


@pytest.mark.mp_group('SESSIONS', 'isolated_serial')
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
        session.login(username=user.username, password=user.password, next='/')
        return session

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
            session = self.spawn_session(user)
            sessions.append(session)
            ws = WSClient(
                session_id=session.session_id,
                csrftoken=session.session.cookies.get('csrftoken')
            ).connect()
            ws.subscribe(control=['limit_reached_{}'.format(user.id)])
            ws_clients.append(ws)
            utils.logged_sleep(3)

        invalid_logins = total - max_logins
        responses = [s.get('/api/v2/me/').status_code for s in sessions]
        assert responses.count(200) == max_logins
        assert responses.count(401) == invalid_logins

        # every *invalid* Websocket client should get a logout notification
        for _ in range(invalid_logins):
            replies = list(ws_clients.pop(0))
            assert len(replies), replies
            assert replies[0].get('user') == user.id, replies
            assert replies[0].get('accept') is True, replies
            assert replies[1].get('group_name') == 'control', replies
            assert replies[1].get('reason') == 'limit_reached', replies

        # every *remaining* Websocket client is valid
        for ws in ws_clients:
            replies = list(ws)
            assert len(replies), replies
            assert replies[0].get('user') == user.id, replies
            assert replies[0].get('accept') is True, replies

    def test_authtoken_maximum_concurrent_sessions_does_not_kick_other_users(self, factories, v2, update_setting_pg):
        update_setting_pg(v2.settings.get().get_endpoint(
            'authentication'), {'SESSIONS_PER_USER': 1})
        org = factories.v2_organization()
        user1, user2 = [factories.v2_user(organization=org) for _ in range(2)]

        sessions = []
        session1 = self.spawn_session(user1)
        sessions.append(session1)
        session2 = self.spawn_session(user2)
        sessions.append(session2)

        responses = [s.get('/api/v2/me/').status_code for s in sessions]
        assert responses.count(200) == 2

    def get_cookie_expiry(self, cookiejar):
        """This uses a Requests cookiejar object -
           http://docs.python-requests.org/en/master/api/#requests.cookies.RequestsCookieJar

           We look for the sessionid cookie and return its expiration time in Unix epoch format"""

        cookies = [c for c in cookiejar if c.name == 'sessionid']
        assert len(cookies) == 1
        return cookies[0].expires

    def test_session_cookie_age_is_applied(self, factories, v2, update_setting_pg):
        user = factories.v2_user()
        update_setting_pg(v2.settings.get().get_endpoint(
            'authentication'), {'SESSION_COOKIE_AGE': 1000})
        session = self.spawn_session(user)
        session.get('/api/v2/me/')
        assert 995 < self.get_cookie_expiry(
            session.session.cookies) - time.time() < 1000

    def test_session_cookie_age_change_affects_active_sessions(self, factories, v2, update_setting_pg):
        user = factories.v2_user()
        session = self.spawn_session(user)

        session.get('/api/v2/me/')
        assert 1795 < self.get_cookie_expiry(
            session.session.cookies) - time.time() < 1800

        update_setting_pg(v2.settings.get().get_endpoint(
            'authentication'), {'SESSION_COOKIE_AGE': 60 * 60 * 24})
        session.get('/api/v2/me/')
        assert 86395 < self.get_cookie_expiry(
            session.session.cookies) - time.time() < 86400
