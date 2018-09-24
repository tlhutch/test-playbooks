import towerkit.exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateCredentialsRBAC(APITest):

    @pytest.mark.parametrize('version', ('v1', 'v2'))
    def test_job_template_creation_request_without_credential_access_forbidden(self, request, factories, version):
        v = request.getfixturevalue(version)
        jt_factory = factories.job_template if version == 'v1' else factories.v2_job_template
        user_factory = factories.user if version == 'v1' else factories.v2_user

        jt_payload = jt_factory.payload()
        organization = jt_payload.ds.inventory.ds.organization

        user = user_factory(organization=organization)

        for resource in ('project', 'inventory'):
            jt_payload.ds[resource].set_object_roles(user, 'use')

        credential = jt_payload.ds.credential

        credential.set_object_roles(user, 'read')
        with self.current_user(user):
            with pytest.raises(exc.Forbidden):
                v.job_templates.post(jt_payload)

        for role in ('use', 'admin'):
            credential.set_object_roles(user, role)
            with self.current_user(user):
                jt = v.job_templates.post(jt_payload)
                jt.delete()

    def test_job_template_creation_request_without_network_credential_access_forbidden(self, request, factories, v1):
        """Verify that a job_template with network credential creation request
        is only permitted if the user making the request has usage permission for the network credential.
        """
        jt_payload = factories.job_template.payload()
        organization = jt_payload.ds.inventory.ds.organization

        user = factories.user(organization=organization)

        for resource in ('credential', 'project', 'inventory'):
            jt_payload.ds[resource].set_object_roles(user, 'use')

        network_credential = factories.credential(kind='net', organization=organization)

        jt_payload.network_credential = network_credential.id

        network_credential.set_object_roles(user, 'read')
        with self.current_user(user):
            with pytest.raises(exc.Forbidden):
                v1.job_templates.post(jt_payload)

        for role in ('use', 'admin'):
            network_credential.set_object_roles(user, role)
            with self.current_user(user):
                jt = v1.job_templates.post(jt_payload)
                jt.delete()

    @pytest.mark.parametrize('version', ('v1', 'v2'))
    def test_job_template_creation_request_without_vault_credential_access_forbidden(self, request, factories, version):
        """Verify that a job_template with network credential creation request
        is only permitted if the user making the request has usage permission for the network credential.
        """
        v = request.getfixturevalue(version)
        jt_factory = factories.job_template if version == 'v1' else factories.v2_job_template
        user_factory = factories.user if version == 'v1' else factories.v2_user

        jt_payload = jt_factory.payload()
        organization = jt_payload.ds.inventory.ds.organization

        user = user_factory(organization=organization)

        for resource in ('credential', 'project', 'inventory'):
            jt_payload.ds[resource].set_object_roles(user, 'use')

        if version == 'v1':
            vault_credential = factories.credential(kind='ssh', vault_password='tower', username='', password='',
                                                    ssh_key_data='', become_password='', organization=organization)
        else:
            vault_credential = factories.v2_credential(kind='vault', vault_password='tower', organization=organization)

        jt_payload.vault_credential = vault_credential.id

        vault_credential.set_object_roles(user, 'read')
        with self.current_user(user):
            with pytest.raises(exc.Forbidden):
                v.job_templates.post(jt_payload)

        for role in ('use', 'admin'):
            vault_credential.set_object_roles(user, role)
            with self.current_user(user):
                jt = v.job_templates.post(jt_payload)
                jt.delete()

    @pytest.mark.parametrize('cred_kind', ('net', 'aws', 'custom'))
    def test_v2_job_template_extra_credential_association_without_credential_access_forbidden(self, request, factories,
                                                                                              cred_kind):
        jt = factories.v2_job_template()
        organization = jt.ds.inventory.ds.organization

        user = factories.user(organization=organization)
        jt.set_object_roles(user, 'admin')

        for resource in ('credential', 'project', 'inventory'):
            jt.ds[resource].set_object_roles(user, 'use')

        if cred_kind == 'custom':
            extra_credential = factories.v2_credential(credential_type=True, organization=organization)
        else:
            extra_credential = factories.v2_credential(kind=cred_kind, organization=organization)

        extra_credential.set_object_roles(user, 'read')
        with self.current_user(user):
            with pytest.raises(exc.Forbidden):
                jt.add_extra_credential(extra_credential)
            assert not jt.related.extra_credentials.get(name=extra_credential.name).count

        for role in ('use', 'admin'):
            extra_credential.set_object_roles(user, role)
            with self.current_user(user):
                jt.add_extra_credential(extra_credential)
                assert jt.related.extra_credentials.get(name=extra_credential.name).count
                jt.remove_extra_credential(extra_credential)
                assert not jt.related.extra_credentials.get(name=extra_credential.name).count

    @pytest.mark.parametrize('version', ('v1', 'v2'))
    def test_launch_with_ask_credential_and_no_credential_access_forbidden(self, factories, version):
        jt_factory = factories.job_template if version == 'v1' else factories.v2_job_template
        user_factory = factories.user if version == 'v1' else factories.v2_user

        jt = jt_factory(ask_credential_on_launch=True)
        credential = jt.ds.credential
        jt.credential = None

        user = user_factory(organization=credential.ds.organization)

        for role in ('execute', 'admin'):
            jt.set_object_roles(user, role)
            with self.current_user(user):
                with pytest.raises(exc.Forbidden):
                    jt.launch(dict(credential=credential.id))
            jt.set_object_roles(user, role, disassociate=True)

    @pytest.mark.parametrize('version', ('v1', 'v2'))
    def test_launch_with_ask_credential_and_no_vault_credential_access_is_forbidden(self, factories, version):
        jt_factory = factories.job_template if version == 'v1' else factories.v2_job_template
        user_factory = factories.user if version == 'v1' else factories.v2_user

        jt = jt_factory(ask_credential_on_launch=True)
        credential = jt.ds.credential
        jt.credential = None

        organization = credential.ds.organization
        user = user_factory(organization=organization)
        credential.set_object_roles(user, 'use')

        if version == 'v1':
            vault_credential = factories.credential(kind='ssh', vault_password='tower', username='', password='',
                                                    ssh_key_data='', become_password='', organization=organization)
        else:
            vault_credential = factories.v2_credential(kind='vault', vault_password='tower', organization=organization)

        for role in ('execute', 'admin'):
            jt.set_object_roles(user, role)
            with self.current_user(user):
                with pytest.raises(exc.Forbidden):
                    jt.launch(dict(credential=credential.id, vault_credential=vault_credential.id))
            jt.set_object_roles(user, role, disassociate=True)

    def test_launch_with_ask_credential_and_no_network_credential_access_is_forbidden(self, factories, v2):
        jt = factories.v2_job_template(ask_credential_on_launch=True)
        credential = jt.ds.credential
        jt.credential = None

        organization = credential.ds.organization
        user = factories.v2_user(organization=organization)
        credential.set_object_roles(user, 'use')

        net_credential = factories.v2_credential(kind='net', organization=organization)

        for role in ('execute', 'admin'):
            jt.set_object_roles(user, role)
            with self.current_user(user):
                with pytest.raises(exc.Forbidden):
                    jt.launch(dict(credential=credential.id, extra_credentials=[net_credential.id]))
            jt.set_object_roles(user, role, disassociate=True)

    def test_launch_with_ask_credential_and_no_extra_credential_access_forbidden(self, factories):
        jt = factories.v2_job_template(ask_credential_on_launch=True)
        credential = jt.ds.credential
        jt.credential = None

        organization = credential.ds.organization

        cloud_credentials = [factories.v2_credential(credential_type=factories.credential_type(),
                                                     organization=organization)]

        user = factories.v2_user(organization=organization)
        credential.set_object_roles(user, 'use')

        for role in ('execute', 'admin'):
            jt.set_object_roles(user, role)
            with self.current_user(user):
                with pytest.raises(exc.Forbidden):
                    jt.launch(dict(credential=credential.id, extra_credentials=[c.id for c in cloud_credentials]))
            jt.set_object_roles(user, role, disassociate=True)

    @pytest.mark.parametrize('version', ('v1', 'v2'))
    def test_relaunch_with_ask_credential_and_no_credential_access_forbidden(self, factories, version):
        jt_factory = factories.job_template if version == 'v1' else factories.v2_job_template
        user_factory = factories.user if version == 'v1' else factories.v2_user

        jt = jt_factory(ask_credential_on_launch=True)
        credential = jt.ds.credential
        jt.credential = None

        user_1 = user_factory(organization=credential.ds.organization)
        user_2 = user_factory()

        for user in (user_1, user_2):
            jt.set_object_roles(user, 'execute')

        credential.set_object_roles(user_1, 'use')

        with self.current_user(user_1):
            job = jt.launch(dict(credential=credential.id)).wait_until_completed()

        with self.current_user(user_2):
            with pytest.raises(exc.Forbidden):
                job.relaunch()

    def test_relaunch_with_ask_credential_and_no_extra_credential_access_forbidden(self, factories):
        host = factories.v2_host()
        organization = host.ds.inventory.ds.organization

        jt = factories.v2_job_template(inventory=host.ds.inventory, ask_credential_on_launch=True)
        credential = jt.ds.credential
        jt.credential = None

        user_1, user_2 = [factories.user(organization=organization) for _ in range(2)]

        cloud_credentials = []
        for i in range(4):
            cloud_credentials.append(factories.v2_credential(name='CloudCredential{}'.format(i),
                                                             credential_type=factories.credential_type(),
                                                             organization=None, user=user_1))

        for user in [user_1, user_2]:
            credential.set_object_roles(user, 'use')
            jt.set_object_roles(user, 'execute')

        with self.current_user(user_1):
            job = jt.launch(dict(credential=credential.id,
                                 extra_credentials=[c.id for c in cloud_credentials[:2]])).wait_until_completed()

        with self.current_user(user_2):
            with pytest.raises(exc.Forbidden):
                job.relaunch(dict(extra_credentials=[c.id for c in cloud_credentials[2:]]))
