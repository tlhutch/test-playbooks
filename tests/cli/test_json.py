import json

import fauxfactory
import pytest
import yaml


@pytest.mark.yolo
@pytest.mark.usefixtures('authtoken')
class TestJSONType(object):

    @pytest.mark.parametrize('resource, expected_doc', [
        ['job_templates', b'--extra_vars JSON/YAML'],
        ['workflow_job_templates', b'--extra_vars JSON/YAML'],
        ['workflow_job_template_nodes', b'--extra_data JSON/YAML'],
        ['inventory', b'--variables JSON/YAML'],
        ['credentials', b'--inputs JSON/YAML'],
        ['credential_types', b'--inputs JSON/YAML'],
        ['credential_types', b'--injectors JSON/YAML'],
    ])
    @pytest.mark.parametrize('action', ['create', 'list'])
    def test_extra_vars_help(self, cli, resource, action, expected_doc):
        params = ['awx', resource, action, '-h']
        result = cli(params, auth=True)
        assert expected_doc in result.stdout

    def test_not_valid_json_or_yaml(self, cli):
        result = cli([
            'awx', 'job_templates', 'create', '--extra_vars', '{"not" valid}'
        ], auth=True)
        assert b'--extra_vars: {"not" valid} is not valid JSON or YAML' in result.stdout

    def test_job_template_extra_vars(self, cli, inventory, project):
        value = {'foo': 'bar'}
        cli(['awx', 'projects', 'update', str(project.id), '--wait'])

        # create it
        result = cli([
            'awx', 'job_templates', 'create', '--inventory', str(inventory.id),
            '--project', str(project.id), '--name', fauxfactory.gen_utf8(),
            '--playbook', 'debug.yml', '--extra_vars', json.dumps(value)
        ], auth=True, teardown=True)
        assert result.returncode == 0
        assert 'id' in result.json
        assert json.loads(result.json['extra_vars']) == {'foo': 'bar'}

        # modify it
        result = cli([
            'awx', 'job_templates', 'modify', str(result.json['id']),
            '--extra_vars', yaml.dump({'spam': 'eggs'})
        ], auth=True)
        assert result.returncode == 0
        assert json.loads(result.json['extra_vars']) == {'spam': 'eggs'}

        # make sure we can filter on it
        error = cli([
            'awx', 'job_templates', 'list', '--extra_vars', json.dumps(value)
        ], auth=True)
        assert error.json['detail'] == 'Filtering on extra_vars is not allowed.'

    def test_workflow_job_template_extra_vars(self, cli, organization):
        value = {'foo': 'bar'}

        # create it
        result = cli([
            'awx', 'workflow_job_templates', 'create', '--organization',
            str(organization.id), '--name', fauxfactory.gen_utf8(),
            '--extra_vars', json.dumps(value)
        ], auth=True, teardown=True)
        assert result.returncode == 0
        assert 'id' in result.json
        assert json.loads(result.json['extra_vars']) == {'foo': 'bar'}

        # modify it
        result = cli([
            'awx', 'workflow_job_templates', 'modify', str(result.json['id']),
            '--extra_vars', yaml.dump(value)
        ], auth=True)
        assert result.returncode == 0
        assert json.loads(result.json['extra_vars']) == {'foo': 'bar'}

    def test_inventory_variables(self, cli, organization):
        value = {'foo': 'bar'}

        # create it
        result = cli([
            'awx', 'inventory', 'create', '--organization',
            str(organization.id), '--name', fauxfactory.gen_utf8(),
            '--variables', json.dumps(value)
        ], auth=True)
        assert result.returncode == 0
        assert 'id' in result.json
        assert json.loads(result.json['variables']) == {'foo': 'bar'}

        # modify it
        result = cli([
            'awx', 'inventory', 'modify', str(result.json['id']),
            '--variables', yaml.dump(value)
        ], auth=True)
        assert result.returncode == 0
        assert json.loads(result.json['variables']) == {'foo': 'bar'}

    def test_credential_inputs(self, cli, organization):
        value = {'username': 'joe', 'password': 'secret'}

        # create it
        result = cli([
            'awx', 'credentials', 'create', '--organization',
            str(organization.id), '--name', fauxfactory.gen_utf8(),
            '--credential_type', '1', '--inputs', json.dumps(value)
        ], auth=True, teardown=True)
        assert result.returncode == 0
        assert 'id' in result.json

        # confirm that password is filtered out
        assert result.json['inputs'] == {
            'username': 'joe', 'password': '$encrypted$'
        }

        # modify it
        result = cli([
            'awx', 'credentials', 'modify', str(result.json['id']),
            '--inputs', yaml.dump({
                'username': 'bob', 'password': '$encrypted$',
            })
        ], auth=True)
        assert result.returncode == 0
        assert result.json['inputs'] == {
            'username': 'bob', 'password': '$encrypted$'
        }

    def test_credential_type_inputs_and_injectors(self, cli):
        inputs = {'fields': []}
        injectors = {'env': {'X_FOO': 'test'}}
        # create it
        result = cli([
            'awx', 'credential_types', 'create', '--name',
            fauxfactory.gen_utf8(), '--kind', 'cloud', '--inputs',
            json.dumps(inputs), '--injectors', json.dumps(injectors)
        ], auth=True, teardown=True)
        assert result.returncode == 0
        assert 'id' in result.json

        assert result.json['inputs'] == inputs
        assert result.json['injectors'] == injectors

        # modify it
        result = cli([
            'awx', 'credential_types', 'modify', str(result.json['id']),
            '--inputs', yaml.dump(inputs), '--injectors', yaml.dump(injectors)
        ], auth=True)
        assert result.returncode == 0
        assert result.json['inputs'] == inputs
        assert result.json['injectors'] == injectors
