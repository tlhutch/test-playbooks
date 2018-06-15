import pytest

from towerkit import exceptions as exc

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_RBAC(Base_Api_Test):

    def test_superuser_can_copy(self, factories):
        v2_inventory_script = factories.v2_inventory_script()
        assert v2_inventory_script.can_copy()

    @pytest.mark.parametrize("is_system_auditor", [True, False])
    def test_users_cannot_copy(self, factories, is_system_auditor):
        v2_notification_template = factories.v2_notification_template()
        user = factories.user(is_system_auditor=is_system_auditor)

        with self.current_user(username=user.username, password=user.password):
            assert not v2_notification_template.can_copy()

            with pytest.raises(exc.Forbidden):
                v2_notification_template.copy()

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_cannot_copy(self, factories, set_test_roles, agent):
        v2_job_template = factories.v2_job_template()
        user = factories.user()
        set_test_roles(user, v2_job_template, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            assert not v2_job_template.can_copy()

            with pytest.raises(exc.Forbidden):
                v2_job_template.copy()
