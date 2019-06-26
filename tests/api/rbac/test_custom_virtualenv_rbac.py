from towerkit import exceptions as exc
from towerkit.utils import random_title
import pytest

from tests.api import APITest

RESOURCES_WITH_VENV = ('job_template', 'project', 'organization')


@pytest.mark.usefixtures('authtoken', 'skip_if_cluster')
class TestCustomVirtualenvRBAC(APITest):

    @pytest.mark.parametrize('resource_name', RESOURCES_WITH_VENV)
    def test_org_admin_can_set_venv_on_org_resources(self, factories, resource_name, create_venv, venv_path, org_admin):
        org = org_admin.related.organizations.get().results.pop()
        other_org = factories.organization()

        if resource_name == 'organization':
            resource = org
            other_resource = other_org
        else:
            resource = getattr(factories, resource_name)()
            other_resource = getattr(factories, resource_name)()

        if resource_name == 'job_template':
            resource.ds.project.organization = org.id
        elif resource_name == 'project':
            resource.organization = org.id

        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            with self.current_user(org_admin):
                resource.custom_virtualenv = venv_path(folder_name)
                json = resource.json
                json.custom_virtualenv = venv_path()
                resource.put(json)

                original_venv = other_resource.custom_virtualenv
                with pytest.raises(exc.Forbidden):
                    other_resource.custom_virtualenv = venv_path(folder_name)
                json = other_resource.json
                json.custom_virtualenv == venv_path(folder_name)
                with pytest.raises(exc.Forbidden):
                    other_resource.put(json)
            assert other_resource.get().custom_virtualenv == original_venv

    @pytest.mark.parametrize('agent,resource_name', [(a, r) for a in ('user', 'team') for r in RESOURCES_WITH_VENV
                                                     if not (a == 'team' and 'organization' in r)])
    def test_admin_role_can_set_venv_on_resource(self, factories, resource_name, agent, create_venv, venv_path,
                                                 set_test_roles):
        user = factories.user()
        resource = getattr(factories, resource_name)()
        set_test_roles(user, resource, agent, 'admin')

        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            json = resource.json
            json.custom_virtualenv = venv_path()
            with self.current_user(user):
                resource.custom_virtualenv = venv_path(folder_name)
                resource.put(json)

    @pytest.mark.parametrize('agent,resource_name', [(a, r) for a in ('user', 'team') for r in RESOURCES_WITH_VENV
                                                     if not (a == 'team' and 'organization' in r)])
    def test_non_admin_roles_cannot_set_venv_on_resource(self, factories, resource_name, agent, create_venv, venv_path,
                                                         set_test_roles):
        user = factories.user()
        resource = getattr(factories, resource_name)()

        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            roles = resource.related.object_roles.get().results
            non_admin_roles = [r.name.lower() for r in roles if r.name.lower() != 'admin']
            for role in non_admin_roles:
                resource.set_object_roles(user, role)
                set_test_roles(user, resource, agent, role)

                original_venv = resource.custom_virtualenv
                json = resource.json
                json.custom_virtualenv = venv_path(folder_name)
                with self.current_user(user):
                    with pytest.raises(exc.Forbidden):
                        resource.custom_virtualenv = venv_path(folder_name)
                    with pytest.raises(exc.Forbidden):
                        resource.put(json)
                assert resource.get().custom_virtualenv == original_venv
                set_test_roles(user, resource, agent, role, disassociate=True)

    @pytest.mark.parametrize('user_type', ['org_user', 'anonymous_user', 'system_auditor'])
    @pytest.mark.parametrize('resource_name', RESOURCES_WITH_VENV)
    def test_non_superuser_and_non_org_admin_roles_cannot_set_venv_on_resource(self, request, factories, resource_name,
                                                                               user_type, create_venv, venv_path):
        user = request.getfixturevalue(user_type)
        resource = getattr(factories, resource_name)()
        if user_type == 'org_user':
            if 'job_template' in resource_name:
                org = resource.ds.project.ds.organization
            elif 'project' in resource_name:
                org = resource.ds.organization
            elif 'organization' in resource_name:
                org = resource
            org.add_user(user)

        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            original_venv = resource.custom_virtualenv
            json = resource.json
            json.custom_virtualenv = venv_path(folder_name)
            with self.current_user(user):
                with pytest.raises(exc.Forbidden):
                    resource.custom_virtualenv = venv_path(folder_name)
                with pytest.raises(exc.Forbidden):
                    resource.put(json)
            assert resource.get().custom_virtualenv == original_venv
