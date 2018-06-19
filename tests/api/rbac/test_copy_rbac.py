from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_RBAC(Base_Api_Test):

    @pytest.fixture(params=('v2_job_template', 'v2_project', 'v2_inventory', 'v2_workflow_job_template',
                            'v2_credential', 'v2_notification_template', 'v2_inventory_script'))
    def resource_name(self, request):
        return request.param

    def test_superuser_can_copy(self, factories, resource_name, copy_for_test):
        resource = getattr(factories, resource_name)()
        assert resource.can_copy()
        copy_for_test(resource)

    def test_non_superuser_cannot_copy(self, factories, non_superuser, resource_name):
        resource = getattr(factories, resource_name)()

        with self.current_user(username=non_superuser.username, password=non_superuser.password):
            assert not resource.can_copy()

            with pytest.raises(exc.Forbidden):
                resource.copy()

    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_resource_admin_cannot_copy(self, factories, resource_name, set_test_roles, agent):
        if resource_name == 'v2_notification_template':
            # notification_template has no object roles
            return

        organization = factories.organization()
        resource = getattr(factories, resource_name)(organization=organization)
        user = factories.user(organization=organization)
        set_test_roles(user, resource, agent, 'admin')

        with self.current_user(username=user.username, password=user.password):
            assert not resource.can_copy()

            with pytest.raises(exc.Forbidden):
                resource.copy()

    def test_org_admin_can_copy_resource_of_same_org(self, factories, resource_name, set_test_roles, copy_for_test):
        organization = factories.organization()
        if resource_name == 'v2_job_template':
            inventory = factories.v2_inventory(organization=organization)
            resource = factories.v2_job_template(inventory=inventory)
        else:
            resource = getattr(factories, resource_name)(organization=organization)
        user = factories.user()
        set_test_roles(user, organization, 'user', 'admin')

        with self.current_user(username=user.username, password=user.password):
            assert resource.can_copy()
            copy_for_test(resource)

    def test_org_admin_cannot_copy_resource_of_other_org(self, factories, resource_name, set_test_roles):
        organization = factories.organization()
        resource = getattr(factories, resource_name)()
        user = factories.user()
        set_test_roles(user, organization, 'user', 'admin')\

        with self.current_user(username=user.username, password=user.password):
            assert not resource.can_copy()

            with pytest.raises(exc.Forbidden):
                resource.copy()
