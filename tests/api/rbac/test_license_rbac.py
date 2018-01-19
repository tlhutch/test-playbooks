import pytest

import towerkit.exceptions
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.mp_group('LicenseRBAC', 'isolated_serial')
@pytest.mark.usefixtures('authtoken')
class Test_License_RBAC(Base_Api_Test):

    def test_delete_as_non_superuser(self, non_superuser, api_config_pg):
        """Verify that DELETE to /api/v1/config/ as a non-superuser raises a 403."""
        with self.current_user(username=non_superuser.username, password=non_superuser.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                api_config_pg.delete()

    def test_post_as_non_superuser(self, non_superuser, api_config_pg):
        """Verify that DELETE to /api/v1/config/ as a non-superuser raises a 403."""
        with self.current_user(username=non_superuser.username, password=non_superuser.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                api_config_pg.post()

    def test_key_visability_as_superuser(self, v2, install_enterprise_license):
        assert 'license_key' in v2.config.get().license_info

    def test_key_visability_as_nonsuperuser(self, v2, install_enterprise_license, non_superusers):
        for user in non_superusers:
            config = v2.config.get()
            if user.is_system_auditor:
                'license_key' in config.license_info
            else:
                'license_key' not in config.license_info
