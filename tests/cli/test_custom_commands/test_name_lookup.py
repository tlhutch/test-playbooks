import fauxfactory
import json
import pytest

from awxkit import utils

from tests.cli.utils import format_error


@pytest.mark.usefixtures('authtoken')
class TestLookupByName(object):

    @pytest.fixture(scope='class')
    def class_resources(self, class_factories, v2_class):
        resources = {}
        resources['users'] = class_factories.user()
        resources['hosts'] = class_factories.host()
        resources['job_templates'] = class_factories.job_template()
        resources['workflow_job_templates'] = class_factories.workflow_job_template()
        resources['instances'] = instance = v2_class.instances.get(rampart_groups__controller__isnull=True).results.pop()
        resources['instance_groups'] = ig = class_factories.instance_group()
        ig.add_instance(instance)
        utils.poll_until(lambda: ig.get().instances == 1, interval=5, timeout=30)
        resources['credentials'] = resources['job_templates'].related.credentials.get()['results'][0]
        resources['projects'] = resources['job_templates'].related.project.get()
        resources['inventory'] = resources['job_templates'].related.inventory.get()
        return resources

    def test_basic_lookup_by_name(self, cli, class_resources):
        for resource, obj in class_resources.items():
            if resource == 'users':
                name = obj.username
            if resource == 'instances':
                name = obj.hostname
            elif resource not in ['users', 'instances']:
                name = obj.name
            result = cli(
                [
                'awx', resource, 'get', str(name), '-f', 'human'
                ],
                auth=True
                )
            assert result.returncode == 0, format_error(result)
            assert name in result.stdout, format_error(result)
            assert str(obj.id)in result.stdout, format_error(result)

    def test_create_job_template_with_named_sub_resources(self, v2, cli, class_resources):
        # make new jt
        jt_name = class_resources['projects'].name.replace('Project', 'Job Template')
        result, jt = cli(
                [
                'awx', 'job_templates', 'create',
                '--project', class_resources['projects'].name,
                '--name', jt_name,
                '--inventory', class_resources['inventory'].name,
                '--instance_group', class_resources['inventory'].name,
                '--playbook', 'ping.yml',
                ],
                auth=True,
                teardown=True,
                return_page=True,
                )
        assert result.returncode == 0, format_error(result)
        assert jt.name == jt_name
        assert jt.related.project.get().id == class_resources['projects'].id
        assert jt.related.inventory.get().id == class_resources['inventory'].id

    def test_lookup_by_camelcase_names(self, cli, ssh_credential, v2, factories):
        hashi_type = v2.credential_types.get(
            managed_by_tower=True,
            name='HashiCorp Vault Secret Lookup'
        ).results.pop()
        hashi_cred = v2.credentials.post(factories.credential.payload(
            name=fauxfactory.gen_utf8(),
            description=fauxfactory.gen_utf8(),
            credential_type=hashi_type,
            inputs={
                'url': 'https://example.org',
                'token': 'some-auth-token',
                'api_version': 'v2',
            },
        ))
        result = cli([
            'awx', 'credential_input_sources', 'create',
            '--target_credential', ssh_credential.name,
            '--source_credential', hashi_cred.name,
            '--input_field_name', 'username',
            '--metadata', json.dumps({
                'secret_path': '/kv/path/',
                'secret_key': 'password',
            })
        ], auth=True)
        assert result.returncode == 0
        result.json['summary_fields']['target_credential']['name'] == ssh_credential.name
        result.json['summary_fields']['source_credential']['name'] == hashi_cred.name
