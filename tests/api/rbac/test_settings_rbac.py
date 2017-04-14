import pytest

import towerkit.exceptions
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_Settings_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_get_main_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        """Verify that a non_superuser can GET the main settings endpoint but that no entries
        are returned.
        """
        with self.current_user(non_superuser.username, non_superuser.password):
            settings_count = api_settings_pg.get().count
            assert settings_count == 0, \
                "Unexpected number of settings returned. Expected zero, got {0}.".format(settings_count)

    def test_get_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        """Verify that non_superusers cannot GET nested settings endpoints (/api/v1/settings/ui/)."""
        for settings_pg in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    settings_pg.get()

    def test_edit_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        """Verify that non_superusers cannot edit nested settings endpoints (/api/v1/settings/ui/)."""
        for settings_pg in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    settings_pg.put()
                with pytest.raises(towerkit.exceptions.Forbidden):
                    settings_pg.patch()

    def test_delete_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        """Verify that non_superusers cannot delete nested settings endpoints (/api/v1/settings/ui/)."""
        for settings_pg in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    settings_pg.delete()
