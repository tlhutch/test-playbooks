from towerkit.api.client import Connection
from towerkit.config import config as qe_config
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
