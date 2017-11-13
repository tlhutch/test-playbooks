from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestSettingsRBAC(Base_Api_Test):

    def test_get_main_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        exp_settings_count = api_settings_pg.get().count
        with self.current_user(non_superuser.username, non_superuser.password):
            if non_superuser.is_system_auditor:
                assert api_settings_pg.get().count == exp_settings_count
            else:
                assert api_settings_pg.get().count == 0

    def test_get_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        for settings in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                if non_superuser.is_system_auditor:
                    settings.get()
                else:
                    with pytest.raises(exc.Forbidden):
                        settings.get()

    def test_edit_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        for settings in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                with pytest.raises(exc.Forbidden):
                    settings.put()
                with pytest.raises(exc.Forbidden):
                    settings.patch()

    def test_delete_nested_endpoint_as_non_superuser(self, non_superuser, api_settings_pg):
        for settings in api_settings_pg.get().results:
            with self.current_user(non_superuser.username, non_superuser.password):
                with pytest.raises(exc.Forbidden):
                    settings.delete()
