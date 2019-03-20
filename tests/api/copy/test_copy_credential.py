from fauxfactory import gen_uuid
import pytest

from tests.api import APITest
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited', 'credential_kind_choices')
class Test_Copy_Credential(APITest):

    identical_fields = ['type', 'description', 'organization', 'credential_type', 'inputs']
    unequal_fields = ['id', 'created', 'modified']

    def test_copy_normal(self, factories, copy_with_teardown):
        v2_credential = factories.v2_credential()
        new_credential = copy_with_teardown(v2_credential)
        check_fields(v2_credential, new_credential, self.identical_fields, self.unequal_fields)

    @pytest.mark.yolo
    def test_check_copied_secret_input(self, factories, copy_with_teardown):
        ct_inputs = {"fields": [{"type": "string", "id": "var1", "label": "Var1", "secret": True}]}
        ct_injectors = {"extra_vars": {"var1": "{{var1}}"}}
        var1_value = gen_uuid()
        cred_input = {"var1": var1_value}

        # Create and copy a credential with injectors
        ct_with_extra_vars = factories.credential_type(kind='net', inputs=ct_inputs, injectors=ct_injectors)
        cred_with_extra_vars = factories.v2_credential(credential_type=ct_with_extra_vars, inputs=cred_input)
        copied_cred = copy_with_teardown(cred_with_extra_vars)
        check_fields(cred_with_extra_vars, copied_cred, self.identical_fields, self.unequal_fields)

        # Create a job template using the copied credential
        host = factories.v2_host()
        job_template = factories.v2_job_template(inventory=host.ds.inventory, playbook="debug_extra_vars.yml")
        job_template.add_credential(copied_cred)

        # Launch the job
        job = job_template.launch().wait_until_completed()
        job.assert_successful()

        # Check the output of the job
        job.related.stdout.get(format='txt_download')
        stdout = job.result_stdout
        assert var1_value in stdout, "Unexpected stdout - {}".format(stdout)
