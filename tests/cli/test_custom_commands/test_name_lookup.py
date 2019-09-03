import pytest

from tests.cli.utils import format_error


@pytest.mark.usefixtures('authtoken')
class TestLookupByName(object):

    @pytest.fixture(scope='class')
    def class_resources(self, class_factories):
        resources = {}
        resources['users'] = class_factories.user()
        resources['hosts'] = class_factories.host()
        resources['job_templates'] = class_factories.job_template()
        resources['workflow_job_templates'] = class_factories.workflow_job_template()
        resources['credentials'] = resources['job_templates'].related.credentials.get()['results'][0]
        resources['projects'] = resources['job_templates'].related.project.get()
        resources['inventory'] = resources['job_templates'].related.inventory.get()
        return resources

    def test_basic_lookup_by_name(self, cli, class_resources):
        for resource, obj in class_resources.items():
            if resource != 'users':
                name = obj.name
                filter = 'id,name'
            else:
                name = obj.username
                filter = 'id,username'
            result = cli(
                [
                'awx', resource, 'get', str(name), '-f', 'human', '--filter', filter,
                ],
                auth=True
                )
            assert result.returncode == 0, format_error(result)
            assert name in result.stdout.decode(encoding='utf-8'), format_error(result)
            assert str(obj.id)in result.stdout.decode(encoding='utf-8'), format_error(result)

    def test_create_job_template_with_named_sub_resources(self, v2, cli, class_resources):
        # make new jt
        jt_name = class_resources['projects'].name.replace('Project', 'Job Template')
        result, jt = cli(
                [
                'awx', 'job_templates', 'create',
                '--project', class_resources['projects'].name,
                '--name', jt_name,
                '--inventory', class_resources['inventory'].name,
                '--credential', class_resources['credentials'].name,
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
        creds = jt.related.credentials.get().results
        assert len(creds) == 1, f'Did not find correct number of credentials, found only {creds}'
        found_cred = creds[0]
        assert found_cred.id == class_resources['credentials'].id
