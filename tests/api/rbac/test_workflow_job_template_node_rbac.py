from towerkit import exceptions as exc
import towerkit.utils as utils
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestWorkflowJobTemplateNodeRBAC(Base_Api_Test):
    def test_credential_association_requires_wfjt_admin_and_jt_execute(self, factories):
        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template(ask_credential_on_launch=True)
        wfn = factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        org = jt.ds.inventory.ds.organization
        ssh_cred = factories.v2_credential(organization=org)
        vault_cred = factories.v2_credential(kind='vault', organization=org, inputs=dict(vault_password='fake'))
        aws_cred, vmware_cred = [factories.v2_credential(kind=kind, organization=org) for kind in ('aws', 'vmware')]
        creds = (ssh_cred, vault_cred, aws_cred, vmware_cred)

        user = factories.v2_user()
        wfjt.set_object_roles(user, 'admin')
        jt.set_object_roles(user, 'execute')
        org.set_object_roles(user, 'member')
        for cred in creds:
            cred.set_object_roles(user, 'admin')

        with self.current_user(user):
            wfn.credential = ssh_cred.id
            for cred in (vault_cred, aws_cred, vmware_cred):
                with utils.suppress(exc.NoContent):
                    wfn.related.credentials.post(dict(id=cred.id))

        assert wfn.credential == ssh_cred.id
        wfn_creds = wfn.related.credentials.get()
        assert wfn_creds.count == 4
        for cred in wfn_creds.results:
            assert cred.id in [cred.id for cred in creds]
