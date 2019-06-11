import pytest
from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestConfigUserAccess(APITest):
    """Verify the /config endpoint displays the expected information based on the current user"""

    def test_privileged_user(self, api_config_pg, privileged_user, user_password):
        """Verify the project_local_paths and project_base_dir fields are present"""
        if privileged_user.username == 'admin':
            user_password = self.credentials['default']['password']

        with self.current_user(username=privileged_user.username, password=user_password):
            conf = api_config_pg.get()
            assert 'project_local_paths' in conf.json
            assert 'project_base_dir' in conf.json

    def test_unprivileged_user(self, api_config_pg, unprivileged_user, user_password):
        """Verify the project_local_paths and project_base_dir fields are absent"""
        with self.current_user(username=unprivileged_user.username, password=user_password):
            conf = api_config_pg.get()
            assert 'project_local_paths' not in conf.json
            assert 'project_base_dir' not in conf.json
