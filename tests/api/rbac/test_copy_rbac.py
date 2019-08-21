from fauxfactory import gen_alpha
from awxkit import exceptions as exc
from awxkit.utils import poll_until
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class Test_Copy_RBAC(APITest):

    copiable_resource_names = ('job_template', 'project', 'inventory', 'workflow_job_template',
                               'credential', 'notification_template', 'inventory_script')

    @pytest.mark.parametrize('resource_name', copiable_resource_names)
    def test_superuser_can_copy(self, factories, resource_name, copy_with_teardown):
        resource = getattr(factories, resource_name)()
        assert resource.can_copy()
        copy_with_teardown(resource)

    @pytest.mark.parametrize('resource_name', copiable_resource_names)
    def test_non_superuser_cannot_copy(self, factories, non_superuser, resource_name, copy_with_teardown):
        resource = getattr(factories, resource_name)()

        with self.current_user(non_superuser):
            if non_superuser.is_system_auditor:
                assert not resource.can_copy()
            else:
                with pytest.raises(exc.Forbidden):
                    resource.can_copy()

            with pytest.raises(exc.Forbidden):
                copy_with_teardown(resource)

    @pytest.mark.parametrize('resource_name', [m for m in copiable_resource_names if m != 'notification_template'])
    @pytest.mark.parametrize('agent', ['user', 'team'])
    def test_resource_admin_cannot_copy(self, factories, resource_name, set_test_roles, agent, copy_with_teardown):
        organization = factories.organization()
        resource = getattr(factories, resource_name)(organization=organization)
        user = factories.user(organization=organization)
        set_test_roles(user, resource, agent, 'admin')

        with self.current_user(user):
            assert not resource.can_copy()

            with pytest.raises(exc.Forbidden):
                copy_with_teardown(resource)

    @pytest.mark.parametrize('resource_name', copiable_resource_names)
    def test_org_admin_can_copy_resource_of_same_org(self, factories, resource_name, copy_with_teardown):
        organization = factories.organization()
        if resource_name == 'job_template':
            inventory = factories.inventory(organization=organization)
            resource = factories.job_template(inventory=inventory)
        else:
            resource = getattr(factories, resource_name)(organization=organization)
        user = factories.user()
        organization.set_object_roles(user, 'admin')

        with self.current_user(user):
            assert resource.can_copy()
            copy_with_teardown(resource)

    def test_can_copy_project_credential_with_use_role(self, factories, copy_with_teardown):
        orgA, orgB = [factories.organization() for _ in range(2)]
        credential = factories.credential(kind='scm', organization=orgA)
        project = factories.project(credential=credential, organization=orgB, wait=False)
        user = factories.user()

        orgA.add_user(user)
        orgB.add_admin(user)
        credential.set_object_roles(user, 'Use')
        with self.current_user(user):
            assert project.can_copy()
            new_project = copy_with_teardown(project)
            assert new_project.related.current_update
            assert new_project.credential == project.credential

    def test_cannot_copy_project_credential_with_read_role(self, factories, copy_with_teardown):
        orgA, orgB = [factories.organization() for _ in range(2)]
        credential = factories.credential(kind='scm', organization=orgA)
        project = factories.project(credential=credential, organization=orgB, wait=False)
        user = factories.user()

        orgA.add_user(user)
        orgB.add_admin(user)
        credential.set_object_roles(user, 'Read')
        with self.current_user(user):
            assert not project.can_copy()
            with pytest.raises(exc.Forbidden):
                copy_with_teardown(project)

    def test_can_copy_inventory_insights_credential_with_use_role(self, factories, copy_with_teardown):
        orgA, orgB = [factories.organization() for _ in range(2)]
        insights_cred = factories.credential(kind='insights', organization=orgA)
        inventory = factories.inventory(organization=orgB, insights_credential=insights_cred.id)
        user = factories.user()

        orgA.add_user(user)
        orgB.add_admin(user)
        insights_cred.set_object_roles(user, 'Use')
        with self.current_user(user):
            assert inventory.can_copy()
            new_inventory = copy_with_teardown(inventory)
            assert new_inventory.insights_credential == inventory.insights_credential

    def test_cannot_copy_inventory_insights_credential_with_read_role(self, factories, copy_with_teardown):
        orgA, orgB = [factories.organization() for _ in range(2)]
        insights_cred = factories.credential(kind='insights', organization=orgA)
        inventory = factories.inventory(organization=orgB, insights_credential=insights_cred.id)
        user = factories.user()

        orgA.add_user(user)
        orgB.add_admin(user)
        insights_cred.set_object_roles(user, 'Read')
        with self.current_user(user):
            assert not inventory.can_copy()
            with pytest.raises(exc.Forbidden):
                copy_with_teardown(inventory)

    # TODO: test unauthorized credential of sources

    def test_can_copy_jt_credentials_with_use_role(self, factories, copy_with_teardown):
        orgA, orgB = [factories.organization() for _ in range(2)]
        vault_cred = factories.credential(kind='vault', vault_password=gen_alpha(), organization=orgA)
        machine_cred = factories.credential(kind='ssh', organization=orgA)
        aws_cred = factories.credential(kind='aws', organization=orgA)
        project = factories.project(organization=orgB)
        inventory = factories.inventory(organization=orgB)
        jt = factories.job_template(inventory=inventory, project=project, credential=None)
        jt.add_credential(aws_cred)
        jt.add_credential(machine_cred)
        jt.add_credential(vault_cred)
        user = factories.user()

        cred_ids = [cred.id for cred in jt.related.credentials.get().results]
        assert vault_cred.id in cred_ids
        assert machine_cred.id in cred_ids
        assert aws_cred.id in cred_ids
        assert len(cred_ids) == 3

        orgA.add_user(user)
        orgB.add_admin(user)
        [cred.set_object_roles(user, "Use") for cred in (vault_cred, machine_cred, aws_cred)]
        with self.current_user(user):
            assert jt.can_copy()
            new_jt = copy_with_teardown(jt)
            new_jt_creds = [c.id for c in new_jt.related.credentials.get().results]
            assert sorted(new_jt_creds) == sorted(cred_ids)

    def test_cannot_copy_jt_credentials_with_read_role(self, factories, copy_with_teardown):
        orgA, orgB = [factories.organization() for _ in range(2)]
        vault_cred = factories.credential(kind='vault', vault_password=gen_alpha(), organization=orgA)
        machine_cred = factories.credential(kind='ssh', organization=orgA)
        aws_cred = factories.credential(kind='aws', organization=orgA)
        project = factories.project(organization=orgB)
        inventory = factories.inventory(organization=orgB)
        jt = factories.job_template(inventory=inventory, project=project, credential=None)
        jt.add_credential(aws_cred)
        jt.add_credential(machine_cred)
        jt.add_credential(vault_cred)
        user = factories.user()

        orgA.add_user(user)
        orgB.add_admin(user)
        [cred.set_object_roles(user, "Read") for cred in (vault_cred, machine_cred, aws_cred)]
        with self.current_user(user):
            assert not jt.can_copy()
            with pytest.raises(exc.Forbidden):
                copy_with_teardown(jt)

    def test_copy_wfjt_node_references_with_permissions(self, factories, copy_with_teardown):
        orgA, orgB = [factories.organization() for _ in range(2)]
        cred = factories.credential(kind='ssh', organization=orgA)
        inv = factories.inventory(organization=orgA)
        jt = factories.job_template(ask_credential_on_launch=True, ask_inventory_on_launch=True, inventory=inv)
        wfjt = factories.workflow_job_template(organization=orgB)
        wfjtn = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                        inventory=inv)
        wfjtn.add_credential(cred)  # JT already has a machine credential, but this is a different one
        assert wfjtn.unified_job_template == jt.id
        assert wfjtn.inventory == inv.id
        wfjtn_creds = [c.id for c in wfjtn.related.credentials.get().results]
        assert wfjtn_creds == [cred.id]
        user = factories.user()

        orgA.add_user(user)
        orgB.add_admin(user)
        jt.set_object_roles(user, "Execute")
        inv.set_object_roles(user, "Use")
        cred.set_object_roles(user, "Use")
        with self.current_user(user):
            assert wfjt.can_copy()
            new_wfjt = copy_with_teardown(wfjt)
            poll_until(lambda: new_wfjt.related.workflow_nodes.get().count == 1, timeout=30)
            new_wfjtn = new_wfjt.related.workflow_nodes.get().results[0]
            assert wfjtn.unified_job_template == new_wfjtn.unified_job_template
            assert wfjtn.inventory == new_wfjtn.inventory
            wfjtn_creds = [c.id for c in wfjtn.related.credentials.get().results]
            new_wfjtn_creds = [c.id for c in new_wfjtn.related.credentials.get().results]
            assert wfjtn_creds == new_wfjtn_creds

    def test_copy_wfjt_node_references_without_permission(self, factories, copy_with_teardown):
        orgA, orgB = [factories.organization() for _ in range(2)]
        cred = factories.credential(kind='ssh', organization=orgA)
        inv = factories.inventory(organization=orgA)
        jt = factories.job_template(ask_credential_on_launch=True, ask_inventory_on_launch=True,
                                       inventory=inv)
        wfjt = factories.workflow_job_template(organization=orgB)
        wfjtn = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                        inventory=inv)
        wfjtn.add_credential(cred)  # JT already has a machine credential, but this is a different one
        assert wfjtn.unified_job_template == jt.id
        assert wfjtn.inventory == inv.id
        wfjtn_creds = [c.id for c in wfjtn.related.credentials.get().results]
        assert wfjtn_creds == [cred.id]
        user = factories.user()

        orgA.add_user(user)
        orgB.add_admin(user)
        jt.set_object_roles(user, "Read")
        inv.set_object_roles(user, "Read")
        cred.set_object_roles(user, "Read")
        with self.current_user(user):
            new_wfjt = copy_with_teardown(wfjt)
            poll_until(lambda: new_wfjt.related.workflow_nodes.get().count == 1, timeout=30)
            new_wfjtn = new_wfjt.related.workflow_nodes.get().results[0]
            assert not new_wfjtn.unified_job_template
            assert not new_wfjtn.inventory
            assert not new_wfjtn.get_related('credentials').count
