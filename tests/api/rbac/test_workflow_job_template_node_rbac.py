from towerkit import exceptions as exc
import towerkit.utils as utils
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestWorkflowJobTemplateNodeRBAC(APITest):
    def test_credential_association_requires_wfjt_admin_and_jt_execute(self, factories):
        wfjt = factories.workflow_job_template()
        jt = factories.job_template(ask_credential_on_launch=True)
        wfjtn = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        wfjtn.remove_all_credentials()

        org = jt.ds.inventory.ds.organization
        ssh_cred = factories.credential(organization=org)
        vault_cred = factories.credential(kind='vault', organization=org, inputs=dict(vault_password='fake'))
        aws_cred, vmware_cred = [factories.credential(kind=kind, organization=org) for kind in ('aws', 'vmware')]
        creds = (ssh_cred, vault_cred, aws_cred, vmware_cred)
        cred_ids = [cred.id for cred in creds]

        user = factories.user()
        org.set_object_roles(user, 'member')
        for cred in creds:
            cred.set_object_roles(user, 'admin')

        # unprivileged users cannot add credentials
        with self.current_user(user):
            with pytest.raises(exc.Forbidden):
                wfjtn.add_credential(ssh_cred)
            for cred in (vault_cred, aws_cred, vmware_cred):
                with pytest.raises(exc.Forbidden):
                    wfjtn.related.credentials.post(dict(id=cred.id))

        # privileged users can add credentials
        wfjt.set_object_roles(user, 'admin')
        jt.set_object_roles(user, 'execute')

        with self.current_user(user):
            wfjtn.add_credential(ssh_cred)
            for cred in (vault_cred, aws_cred, vmware_cred):
                with utils.suppress(exc.NoContent):
                    wfjtn.related.credentials.post(dict(id=cred.id))

        wfjtn_creds = [c.id for c in wfjtn.related.credentials.get().results]
        assert sorted(wfjtn_creds) == sorted(cred_ids)
        wfjtn_creds = wfjtn.related.credentials.get()
        assert wfjtn_creds.count == 4
        for cred in wfjtn_creds.results:
            assert cred.id in cred_ids
