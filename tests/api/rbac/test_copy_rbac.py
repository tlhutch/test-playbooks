from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_RBAC(Base_Api_Test):

    copiable_resource_names = ('v2_job_template', 'v2_project', 'v2_inventory', 'v2_workflow_job_template',
                               'v2_credential', 'v2_notification_template', 'v2_inventory_script')

    @pytest.mark.parametrize('resource_name', copiable_resource_names)
    def test_superuser_can_copy(self, factories, resource_name, copy_with_teardown):
        resource = getattr(factories, resource_name)()
        assert resource.can_copy()
        copy_with_teardown(resource)

    @pytest.mark.parametrize('resource_name', copiable_resource_names)
    def test_non_superuser_cannot_copy(self, factories, non_superuser, resource_name):
        resource = getattr(factories, resource_name)()

        with self.current_user(non_superuser):
            assert not resource.can_copy()

            with pytest.raises(exc.Forbidden):
                resource.copy()

    @pytest.mark.parametrize('resource_name', [m for m in copiable_resource_names if m != 'v2_notification_template'])
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_resource_admin_cannot_copy(self, factories, resource_name, set_test_roles, agent):
        organization = factories.organization()
        resource = getattr(factories, resource_name)(organization=organization)
        user = factories.user(organization=organization)
        set_test_roles(user, resource, agent, 'admin')

        with self.current_user(user):
            assert not resource.can_copy()

            with pytest.raises(exc.Forbidden):
                resource.copy()

    @pytest.mark.parametrize('resource_name', copiable_resource_names)
    def test_org_admin_can_copy_resource_of_same_org(self, factories, resource_name, set_test_roles, copy_with_teardown):
        organization = factories.organization()
        if resource_name == 'v2_job_template':
            inventory = factories.v2_inventory(organization=organization)
            resource = factories.v2_job_template(inventory=inventory)
        else:
            resource = getattr(factories, resource_name)(organization=organization)
        user = factories.user()
        set_test_roles(user, organization, 'user', 'admin')

        with self.current_user(user):
            assert resource.can_copy()
            copy_with_teardown(resource)

    @pytest.mark.parametrize('resource_name', copiable_resource_names)
    def test_org_admin_cannot_copy_resource_of_other_org(self, factories, resource_name, set_test_roles):
        organization = factories.organization()
        resource = getattr(factories, resource_name)()
        user = factories.user()
        set_test_roles(user, organization, 'user', 'admin')

        with self.current_user(user):
            assert not resource.can_copy()

            with pytest.raises(exc.Forbidden):
                resource.copy()
