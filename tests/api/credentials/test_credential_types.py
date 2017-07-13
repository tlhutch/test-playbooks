from towerkit.utils import credential_type_kinds, PseudoNamespace
from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.ha_tower
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCredentialTypes(Base_Api_Test):

    def test_credential_type_options(self, v2):
        """confirms that OPTIONS for credential types provides desired information for type creation and retrieval"""
        options = v2.credential_types.options()

        kind = options.actions.POST.kind
        assert 'default' not in kind
        assert kind.required is True
        assert kind.type == 'choice'
        assert kind.label == 'Kind'
        assert set([choice[0] for choice in kind.choices]) == set(credential_type_kinds)

        inputs = options.actions.POST.inputs
        assert inputs.default == {}
        assert inputs.required is False
        assert inputs.type == 'field'
        assert inputs.label == 'Inputs'

        injectors = options.actions.POST.injectors
        assert injectors.default == {}
        assert injectors.required is False
        assert injectors.type == 'field'
        assert injectors.label == 'Injectors'

    def test_confirm_empty_defaults_for_credential_type(self, factories):
        for kind in credential_type_kinds:
            cred_type = factories.credential_type(kind=kind)
            assert cred_type.kind == kind
            assert cred_type.inputs == {}
            assert cred_type.injectors == {}
            assert not cred_type.managed_by_tower

    @pytest.fixture(scope='class')
    def managed_by_tower_fields(self, v2_class):
        managed_by_tower = v2_class.credential_types.get(managed_by_tower=True).results
        managed_by_tower_fields = {}
        for cred_type in managed_by_tower:
            field_values = PseudoNamespace()
            managed_by_tower_fields[cred_type.name] = field_values
            field_values['kind'] = cred_type.kind
            for field in cred_type.inputs.fields:
                field_values[field['id']] = field
                field.pop('id')
        return managed_by_tower_fields

    def test_managed_by_tower_aws_credential_type(self, managed_by_tower_fields):
        aws = managed_by_tower_fields['Amazon Web Services']
        assert aws.kind == 'cloud'
        assert aws.password.label == 'Secret Key'
        assert aws.password.secret is True
        assert aws.security_token.label == 'STS Token'
        assert aws.security_token.secret is True
        assert aws.username.label == 'Access Key'

    def test_managed_by_tower_azure_classic_credential_type(self, managed_by_tower_fields):
        azure = managed_by_tower_fields['Microsoft Azure Classic (deprecated)']
        assert azure.kind == 'cloud'
        assert azure.ssh_key_data.format == 'ssh_private_key'
        assert azure.ssh_key_data.label == 'Management Certificate'
        assert azure.ssh_key_data.multiline is True
        assert azure.ssh_key_data.secret is True
        assert azure.username.label == 'Subscription ID'

    def test_managed_by_tower_azure_rm_credential_type(self, managed_by_tower_fields):
        azure = managed_by_tower_fields['Microsoft Azure Resource Manager']
        assert azure.kind == 'cloud'
        assert azure.client.label == 'Client ID'
        assert azure.password.label == 'Password'
        assert azure.password.secret is True
        assert azure.secret.label == 'Client Secret'
        assert azure.secret.secret is True
        assert azure.subscription.label == 'Subscription ID'
        assert azure.tenant.label == 'Tenant ID'
        assert azure.username.label == 'Username'

    def test_managed_by_tower_cloudforms_credential_type(self, managed_by_tower_fields):
        cloudforms = managed_by_tower_fields['Red Hat CloudForms']
        assert cloudforms.kind == 'cloud'
        assert cloudforms.host.label == 'CloudForms URL'
        assert cloudforms.password.label == 'Password'
        assert cloudforms.password.secret is True
        assert cloudforms.username.label == 'Username'

    def test_managed_by_tower_gce_credential_type(self, managed_by_tower_fields):
        gce = managed_by_tower_fields['Google Compute Engine']
        assert gce.kind == 'cloud'
        assert gce.project.label == 'Project'
        assert gce.ssh_key_data.format == 'ssh_private_key'
        assert gce.ssh_key_data.label == 'RSA Private Key'
        assert gce.ssh_key_data.multiline is True
        assert gce.ssh_key_data.secret is True
        assert gce.username.label == 'Service Account Email Address'

    def test_managed_by_tower_insights_credential_type(self, managed_by_tower_fields):
        insights = managed_by_tower_fields['Insights']
        assert insights.kind == 'insights'
        assert insights.password.label == 'Password'
        assert insights.password.secret is True
        assert insights.username.label == 'Username'

    def test_managed_by_tower_openstack_credential_type(self, managed_by_tower_fields):
        openstack = managed_by_tower_fields['OpenStack']
        assert openstack.kind == 'cloud'
        assert openstack.domain.label == 'Domain Name'
        assert openstack.host.label == 'Host (Authentication URL)'
        assert openstack.password.label == 'Password (API Key)'
        assert openstack.password.secret is True
        assert openstack.project.label == 'Project (Tenant Name)'
        assert openstack.username.label == 'Username'

    def test_managed_by_tower_network_credential_type(self, managed_by_tower_fields):
        net = managed_by_tower_fields['Network']
        assert net.kind == 'net'
        assert net.authorize.label == 'Authorize'
        assert net.authorize.type == 'boolean'
        assert net.authorize_password.label == 'Authorize Password'
        assert net.authorize_password.secret is True
        assert net.password.label == 'Password'
        assert net.password.secret is True
        assert net.ssh_key_data.format == 'ssh_private_key'
        assert net.ssh_key_data.label == 'SSH Private Key'
        assert net.ssh_key_data.multiline is True
        assert net.ssh_key_data.secret is True
        assert net.ssh_key_unlock.label == 'Private Key Passphrase'
        assert net.ssh_key_unlock.secret is True
        assert net.username.label == 'Username'

    def test_managed_by_tower_satellite_credential_type(self, managed_by_tower_fields):
        satellite = managed_by_tower_fields['Red Hat Satellite 6']
        assert satellite.kind == 'cloud'
        assert satellite.host.label == 'Satellite 6 URL'
        assert satellite.password.label == 'Password'
        assert satellite.password.secret is True
        assert satellite.username.label == 'Username'

    def test_managed_by_tower_scm_credential_type(self, managed_by_tower_fields):
        scm = managed_by_tower_fields['Source Control']
        assert scm.kind == 'scm'
        assert scm.password.label == 'Password'
        assert scm.password.secret is True
        assert scm.ssh_key_data.format == 'ssh_private_key'
        assert scm.ssh_key_data.label == 'SCM Private Key'
        assert scm.ssh_key_data.multiline is True
        assert scm.ssh_key_data.secret is True
        assert scm.ssh_key_unlock.label == 'Private Key Passphrase'
        assert scm.ssh_key_unlock.secret is True
        assert scm.username.label == 'Username'

    def test_managed_by_tower_ssh_credential_type(self, managed_by_tower_fields):
        ssh = managed_by_tower_fields['SSH']
        assert ssh.kind == 'ssh'
        assert set(ssh.become_method.choices) == set(['', 'sudo', 'su', 'pbrun', 'pfexec', 'dzdo', 'pmrun'])
        assert ssh.become_method.label == 'Privilege Escalation Method'
        assert ssh.become_password.ask_at_runtime is True
        assert ssh.become_password.label == 'Privilege Escalation Password'
        assert ssh.become_password.secret is True
        assert ssh.become_username.label == 'Privilege Escalation Username'
        assert ssh.password.ask_at_runtime is True
        assert ssh.password.label == 'Password'
        assert ssh.password.secret is True
        assert ssh.ssh_key_data.format == 'ssh_private_key'
        assert ssh.ssh_key_data.label == 'SSH Private Key'
        assert ssh.ssh_key_data.multiline is True
        assert ssh.ssh_key_data.secret is True
        assert ssh.ssh_key_unlock.ask_at_runtime is True
        assert ssh.ssh_key_unlock.label == 'Private Key Passphrase'
        assert ssh.ssh_key_unlock.secret is True
        assert ssh.username.label == 'Username'

    def test_managed_by_tower_vault_credential_type(self, managed_by_tower_fields):
        vault = managed_by_tower_fields['Vault']
        assert vault.kind == 'vault'
        assert vault.vault_password.ask_at_runtime is True
        assert vault.vault_password.label == 'Vault Password'
        assert vault.vault_password.secret is True

    def test_managed_by_tower_vmware_credential_type(self, managed_by_tower_fields):
        vmware = managed_by_tower_fields['VMware vCenter']
        assert vmware.kind == 'cloud'
        assert vmware.host.label == 'VCenter Host'
        assert vmware.password.label == 'Password'
        assert vmware.password.secret is True
        assert vmware.username.label == 'Username'

    managed_credential_type_modification_disallowed = 'Modifications not allowed for managed credential types'
    managed_credential_type_deletion_disallowed = 'Deletion not allowed for managed credential types'

    def test_managed_by_tower_credential_types_are_read_only(self, v2):
        """Confirms that managed_by_tower credential types cannot be edited or deleted"""
        managed_by_tower = v2.credential_types.get(managed_by_tower=True).results

        for cred_type in managed_by_tower:
            with pytest.raises(exc.Forbidden) as e:
                cred_type.patch(name='Uh-oh!')
            assert e.value.message['detail'] == self.managed_credential_type_modification_disallowed

            with pytest.raises(exc.Forbidden) as e:
                cred_type.put()
            assert e.value.message['detail'] == self.managed_credential_type_modification_disallowed

            with pytest.raises(exc.Forbidden) as e:
                cred_type.delete()
            assert e.value.message['detail'] == self.managed_credential_type_deletion_disallowed


    def test_sourced_credential_type_cannot_be_deleted(self, factories):
        cred = factories.v2_credential(credential_type=True)

        with pytest.raises(exc.Forbidden) as e:
            cred.ds.credential_type.delete()
        assert e.value.message['detail'] == self.managed_credential_type_deletion_disallowed

    def test_sourced_credential_type_inputs_are_read_only(self, factories):
        cred = factories.v2_credential(credential_type=True)

        with pytest.raises(exc.Forbidden) as e:
            cred.ds.credential_type.inputs = dict(test=True)
        assert e.value.message['detail'] == self.managed_credential_type_modification_disallowed

    def test_confirm_non_cloud_or_network_credential_kinds_disallowed(self, factories):
        for kind in ('insights', 'scm', 'ssh', 'vault'):
            with pytest.raises(exc.BadRequest) as e:
                factories.credential_type(kind=kind)
            assert e.value.message == {'kind': ["Must be 'cloud' or 'net', not {}".format(kind)]}

        with pytest.raises(exc.BadRequest) as e:
            factories.credential_type(kind='not_a_kind')
        assert e.value.message == {'kind': ['"not_a_kind" is not a valid choice.']}

    @pytest.mark.parametrize('fields, expected_error', [[[dict(label='Label')], ["'id' is a required property"]],
                                                        [[dict(id='field_id')], ["'label' is a required property"]]])
    def test_confirm_input_properties_are_required_property(self, factories, fields, expected_error):
        with pytest.raises(exc.BadRequest) as e:
            factories.credential_type(inputs=dict(fields=fields))
        assert e.value.message['inputs'] == expected_error

    @pytest.mark.parametrize('field, value', [('multiline', True), ('multiline', False),
                                              ('format', 'ssh_private_key'),
                                              ('choices', ['1', '2', '3', '4'])])
    def test_confirm_invalid_input_fields_with_boolean(self, factories, field, value):
        invalid = {}
        invalid[field] = value
        desired_message = ["{0} not allowed for boolean type (field_id)".format(field)]
        with pytest.raises(exc.BadRequest) as e:
            factories.credential_type(inputs=dict(fields=[dict(id='field_id', label='Label',
                                                               type='boolean', **invalid)]))
        assert e.value.message['inputs'] == desired_message

    def test_confirm_injector_sourced_input_must_exist(self, factories):
        env_var_one = dict(id='env_var_one', label='EnvVarOne')
        inputs = dict(fields=[env_var_one])

        extra_vars = dict(extra_var_one='{{extra_var_one}}',
                          extra_var_two='{{extra_var_two}}')
        injectors = dict(extra_vars=extra_vars)

        with pytest.raises(exc.BadRequest) as e:
            factories.credential_type(inputs=inputs, injectors=injectors)
        assert e.value.message['injectors'] == ["extra_var_one uses an undefined field ('extra_var_one' is undefined)"]

    @pytest.mark.parametrize('field, malformed', [('inputs', dict(inputs=[1, 2, 3, 4])),
                                                  ('inputs', dict(inputs='malformed')),
                                                  ('inputs', dict(inputs=dict(fields=[123, 234, 345]))),
                                                  ('inputs', dict(inputs=dict(fields=[dict(id='one', label='One'),
                                                                                      234]))),
                                                  ('injectors', dict(injectors=[1, 2, 3, 4])),
                                                  ('injectors', dict(injectors='malformed')),
                                                  ('injectors', dict(injectors=dict(mal='formed'))),
                                                  ('injectors', dict(injectors=dict(env=dict(ENV_VAR=123),
                                                                                             mal='formed')))])
    def test_confirm_bad_request_on_malformed_fields(self, factories, field, malformed):
        with pytest.raises(exc.BadRequest) as e:
            factories.credential_type(**malformed)
        message = e.value.message[field][0]
        assert 'is not of type' in message or 'Additional properties are not allowed' in message

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/6769')
    def test_confirm_inputs_persist_as_specified(self, factories):
        field_one = dict(id='field_one', type='string', label='FieldOne', secret=True,
                         help_text='FieldOne Help Text')
        field_two = dict(id='field_two', type='string', label='FieldTwo', secret=True,
                         multiline=True, help_text='FieldTwo Help Text')
        field_three = dict(id='field_three', type='string', label='FieldThree', secret=False,
                           help_text='FieldThree Help Text')
        field_four = dict(id='field_four', type='string', label='FieldFour', secret=False,
                          multiline=True, help_text='FieldFour Help Text')
        field_five = dict(id='field_five', type='boolean', label='FieldFive', secret=False,
                          help_text='FieldFive Help Text')
        field_six = dict(id='field_six', type='boolean', label='FieldSix', secret=True,
                        help_text='FieldSix Help Text')
        inputs = dict(fields=[field_one, field_two, field_three, field_four, field_five, field_six],
                      required=['field_one', 'field_two', 'field_three'])

        cred_type = factories.credential_type(inputs=inputs)
        assert cred_type.inputs == inputs
        cred_type.get()  # We previously inspected POST response content
        assert cred_type.inputs == inputs

    def test_confirm_injectors_persist_as_specified(self, factories):
        env_var_one = dict(id='env_var_one', label='EnvVarOne')
        env_var_two = dict(id='env_var_two', label='EnvVarTwo')
        extra_var_one = dict(id='extra_var_one', label='ExtraVarOne')
        extra_var_two = dict(id='extra_var_two', label='ExtraVarTwo')
        what = dict(id='what', label='What?')
        inputs = dict(fields=[env_var_one, env_var_two, extra_var_one, extra_var_two, what])

        env = dict(ENV_VAR_ONE='{{env_var_one}}',
                   ENV_VAR_TWO='{{env_var_two}}')
        extra_vars = dict(extra_var_one='{{extra_var_one}}',
                          extra_var_two='{{extra_var_two}}')
        file = dict(template="[temp_cred]\nmy_name_is={{what}}\n")
        injectors = dict(env=env, extra_vars=extra_vars, file=file)

        cred_type = factories.credential_type(inputs=inputs, injectors=injectors)
        assert cred_type.injectors == injectors
        cred_type.get()  # We previously inspected POST response content
        assert cred_type.injectors == injectors


@pytest.mark.api
@pytest.mark.ha_tower
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCredentialTypesActivityStream(Base_Api_Test):

    def test_credential_type_activity_stream_create(self, factories):
        cred_type = factories.credential_type()
        activity_stream = cred_type.related.activity_stream.get()
        assert activity_stream.count == 1
        event = activity_stream.results.pop()
        assert event.operation == 'create'
        assert event.object1 == 'credential_type'
        changes = event.changes
        assert changes.kind == cred_type.kind
        assert changes.inputs == str(cred_type.inputs)
        assert changes.injectors == str(cred_type.injectors)
        assert changes.name == cred_type.name
        assert changes.description == cred_type.description
        assert changes.id == cred_type.id
