import towerkit.exceptions as exc
import pytest
import yaml

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.ha_tower
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCustomCredentials(Base_Api_Test):

    @pytest.mark.parametrize('field_type', ['string', 'boolean'])
    def test_unprovided_required_input_field(self, factories, field_type):
        inputs = dict(fields=[dict(id='field', label='Field', type=field_type)], required=['field'])
        credential_type = factories.credential_type(inputs=inputs)

        with pytest.raises(exc.BadRequest) as e:
            factories.v2_credential(credential_type=credential_type, inputs={})
        assert e.value.message == {'inputs': {'field': ["required for {0.name}".format(credential_type)]}}

    def test_extraneous_input_field(self, factories):
        inputs = dict(fields=[dict(id='field', label='Field')])
        credential_type = factories.credential_type(inputs=inputs)

        with pytest.raises(exc.BadRequest) as e:
            factories.v2_credential(credential_type=credential_type,
                                    inputs=dict(not_a_field=123))
        desired = {'inputs': ["Additional properties are not allowed (u'not_a_field' was unexpected)"]}
        assert e.value.message == desired

    def test_non_boolean_input_for_boolean_field(self, factories):
        inputs = dict(fields=[dict(id='field', label='Field', type='boolean')])
        credential_type = factories.credential_type(inputs=inputs)

        with pytest.raises(exc.BadRequest) as e:
            factories.v2_credential(credential_type=credential_type,
                                    inputs=dict(field=123))
        assert e.value.message == {'inputs': {'field': ["123 is not of type u'boolean'"]}}

        with pytest.raises(exc.BadRequest) as e:
            factories.v2_credential(credential_type=credential_type,
                                    inputs=dict(field='string'))
        assert e.value.message == {'inputs': {'field': ["u'string' is not of type u'boolean'"]}}

    def test_extra_var_injector_variables_in_job_args_and_event_data(self, factories):
        inputs = dict(fields=[dict(id='field_one', label='FieldOne', secret=True),
                              dict(id='field_two', label='FieldTwo', type='string')])
        injectors = dict(extra_vars=dict(extra_var_from_field_one='{{ field_one }}',
                                         extra_var_from_field_two='{{ field_two }}'))
        credential_type = factories.credential_type(inputs=inputs, injectors=injectors)

        input_values = dict(field_one='FieldOneVal', field_two='123')
        field_to_var = dict(field_one='extra_var_from_field_one', field_two='extra_var_from_field_two')
        credential = factories.v2_credential(credential_type=credential_type, inputs=input_values)

        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, credential=credential,
                                       playbook='debug_hostvars.yml')
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        job_args = [yaml.load(item) for item in yaml.load(job.job_args)]
        assert dict(extra_var_from_field_one='**********', extra_var_from_field_two='123') in job_args

        hostvars = job.related.job_events.get(host=host.id, task='debug').results.pop().event_data.res.hostvars
        for field, value in input_values.items():
            assert hostvars[host.name][field_to_var[field]] == value

    def test_env_var_injector_variables_in_job_env_and_ansible_env(self, factories):
        inputs = dict(fields=[dict(id='field_one', label='FieldOne', secret=True),
                              dict(id='field_two', label='FieldTwo', type='string')])
        injectors = dict(env=dict(EXTRA_VAR_FROM_FIELD_ONE='{{ field_one }}',
                                  EXTRA_VAR_FROM_FIELD_TWO='{{ field_two }}'))
        credential_type = factories.credential_type(inputs=inputs, injectors=injectors)

        credential = factories.v2_credential(credential_type=credential_type,
                                             inputs=dict(field_one='FieldOneVal', field_two='True'))

        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, credential=credential,
                                       playbook='ansible_env.yml')
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        assert job.job_env.EXTRA_VAR_FROM_FIELD_ONE == '**********'
        assert job.job_env.EXTRA_VAR_FROM_FIELD_TWO == 'True'

        ansible_env = job.related.job_events.get(host=host.id, task='debug').results.pop().event_data.res.ansible_env
        assert ansible_env.EXTRA_VAR_FROM_FIELD_ONE == 'FieldOneVal'
        assert ansible_env.EXTRA_VAR_FROM_FIELD_TWO == 'True'

    @pytest.mark.parametrize('injector_var',
                             [dict(extra_vars=dict(file_to_cat='{{ tower.filename }}')),
                              dict(env=dict(AP_FILE_TO_CAT='{{ tower.filename }}'))],
                             ids=('extra_var', 'env_var'))
    def test_file_injector_path_from_variable(self, factories, injector_var):
        file_contents = 'THIS IS A FILE!'
        injectors = dict(file=dict(template=file_contents))
        injectors.update(injector_var)
        credential_type = factories.credential_type(injectors=injectors)

        credential = factories.v2_credential(credential_type=credential_type)

        host = factories.v2_host()
        jt = factories.v2_job_template(inventory=host.ds.inventory, credential=credential,
                                       playbook='cat_file.yml')
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        stdout = job.related.job_events.get(host=host.id, task='debug').results.pop().event_data.res.cat.stdout
        assert stdout == file_contents
