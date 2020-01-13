from fauxfactory import gen_uuid, gen_utf8
import pytest

from tests.api import APITest
from tests.lib.helpers.copy_utils import check_fields
from tests.api.credentials.test_credential_plugins import TestHashiCorpVaultCredentials
from awxkit.config import config


@pytest.mark.usefixtures('authtoken')
class Test_Copy_Credential(APITest):

    identical_fields = ['type', 'description', 'organization', 'credential_type', 'inputs']
    unequal_fields = ['id', 'created', 'modified']

    def test_copy_normal(self, factories, copy_with_teardown):
        credential = factories.credential()
        new_credential = copy_with_teardown(credential)
        check_fields(credential, new_credential, self.identical_fields, self.unequal_fields)

    @pytest.mark.yolo
    def test_check_copied_secret_input(self, factories, copy_with_teardown):
        ct_inputs = {"fields": [{"type": "string", "id": "var1", "label": "Var1", "secret": True}]}
        ct_injectors = {"extra_vars": {"var1": "{{var1}}"}}
        var1_value = gen_uuid()
        cred_input = {"var1": var1_value}

        # Create and copy a credential with injectors
        ct_with_extra_vars = factories.credential_type(kind='net', inputs=ct_inputs, injectors=ct_injectors)
        cred_with_extra_vars = factories.credential(credential_type=ct_with_extra_vars, inputs=cred_input)
        copied_cred = copy_with_teardown(cred_with_extra_vars)
        check_fields(cred_with_extra_vars, copied_cred, self.identical_fields, self.unequal_fields)

        # Create a job template using the copied credential
        host = factories.host()
        job_template = factories.job_template(inventory=host.ds.inventory, playbook="debug_extra_vars.yml")
        job_template.add_credential(copied_cred)

        # Launch the job
        job = job_template.launch().wait_until_completed()
        job.assert_successful()

        # Check the output of the job
        job.related.stdout.get(format='txt_download')
        stdout = job.result_stdout
        assert var1_value in stdout, "Unexpected stdout - {}".format(stdout)

    @pytest.mark.yolo
    def test_check_copied_input_sources(self, factories, v2, k8s_vault, copy_with_teardown):
        """Test whether copying a credential with lookup sources ignores the lookups.

        This test targets the following issue:

        https://github.com/ansible/awx/issues/4797
        """
        # create a hashicorp vault lookup credential
        hashi = TestHashiCorpVaultCredentials()
        hashi_credential = hashi.create_hashicorp_vault_credential(
            factories, v2, k8s_vault, config.credentials.hashivault.token, 'v1'
        )

        # create a credential using the lookup
        cred_type = v2.credential_types.get(managed_by_tower=True, kind='ssh').results.pop()
        payload = factories.credential.payload(
            name=gen_utf8(),
            description=gen_utf8(),
            credential_type=cred_type
        )
        credential = v2.credentials.post(payload)

        metadata_username = {
            'secret_path': '/kv/example-user/',
            'secret_key': 'username',
        }
        credential.related.input_sources.post(dict(
            input_field_name='username',
            source_credential=hashi_credential.id,
            metadata=metadata_username,
        ))

        # copy credential
        copied_credential = copy_with_teardown(credential)

        copied_input_sources = copied_credential.related.input_sources.get()
        original_input_sources = credential.related.input_sources.get()
        # assert we got same number of inputs
        assert len(copied_input_sources.results) == len(original_input_sources.results)
        # assert we have same input source (the hashicorp vault)
        assert copied_input_sources.results[0].source_credential == original_input_sources.results[0].source_credential
        # assert we have same metadata (the secret key and location)
        assert copied_input_sources.results[0].metadata == original_input_sources.results[0].metadata
        # assert the copied one knows to target itself as the credential to use the input source for
        assert copied_input_sources.results[0].target_credential == copied_credential.id
        # assert it is going to provide the same input filed
        assert copied_input_sources.results[0].input_field_name == original_input_sources.results[0].input_field_name
        # assert the input field is not blank
        assert copied_credential.inputs[copied_input_sources.results[0].input_field_name] != ''

        # run job with copied credential
        host = factories.host()

        jt = factories.job_template(inventory=host.ds.inventory, playbook='ping.yml', credential=None)
        jt.add_credential(copied_credential)
        job = jt.launch().wait_until_completed()
        job.assert_successful()
