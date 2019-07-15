import pytest

import towerkit.exceptions
from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class Test_License_RBAC(APITest):

    def test_delete_as_non_superuser(self, non_superuser, v2):
        """Verify that DELETE to /api/v2/config/ as a non-superuser raises a 403."""
        with self.current_user(username=non_superuser.username, password=non_superuser.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                v2.config.delete()

    def test_post_as_non_superuser(self, non_superuser, v2):
        """Verify that DELETE to /api/v2/config/ as a non-superuser raises a 403."""
        with self.current_user(username=non_superuser.username, password=non_superuser.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                v2.config.post()

    def test_key_visability_as_superuser(self, v2):
        assert 'license_key' in v2.config.get().license_info

    def test_key_visability_as_nonsuperuser(self, v2, non_superusers):
        for user in non_superusers:
            config = v2.config.get()
            if user.is_system_auditor:
                'license_key' in config.license_info
            else:
                'license_key' not in config.license_info
