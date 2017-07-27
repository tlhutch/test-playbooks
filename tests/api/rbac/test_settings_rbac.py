from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class TestSettingsRBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_get_main_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        """Verify that a non_superuser can GET the main settings endpoint but that no entries
        are returned.
        """
        with self.current_user(non_superuser.username, non_superuser.password):
            settings_count = api_settings_pg.get().count
            if non_superuser.is_system_auditor:
                assert settings_count == 16
            else:
                assert settings_count == 0, \
                    "Unexpected number of settings returned. Expected zero, got {0}.".format(settings_count)

    def test_get_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        """Verify that non_superusers cannot GET nested settings endpoints (/api/v1/settings/ui/)."""
        for settings in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                if non_superuser.is_system_auditor:
                    settings.get()
                else:
                    with pytest.raises(exc.Forbidden):
                        settings.get()

    def test_edit_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        """Verify that non_superusers cannot edit nested settings endpoints (/api/v1/settings/ui/)."""
        for settings in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                with pytest.raises(exc.Forbidden):
                    settings.put()
                with pytest.raises(exc.Forbidden):
                    settings.patch()

    def test_delete_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        """Verify that non_superusers cannot delete nested settings endpoints (/api/v1/settings/ui/)."""
        for settings in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                with pytest.raises(exc.Forbidden):
                    settings.delete()
