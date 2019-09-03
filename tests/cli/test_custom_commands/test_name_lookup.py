import pytest

from tests.cli.utils import format_error


@pytest.mark.usefixtures('authtoken')
class TestLookupByName(object):

    def test_lookup_by_name(self, cli, job_template_ping, workflow_job_template):
        resources = {}
        resources['job_templates'] = job_template_ping
        resources['workflow_job_templates'] = workflow_job_template
        resources['credentials'] = job_template_ping.related.credentials.get()['results'][0]
        resources['projects'] = job_template_ping.related.project.get()
        resources['inventory'] = job_template_ping.related.inventory.get()
        for resource, obj in resources.items():
            result = cli(
                [
                'awx', resource, 'get', str(obj.name), '-f', 'human',
                ],
                auth=True
                )
            assert result.returncode == 0, format_error(result)
            assert obj.name in result.stdout.decode(encoding='utf-8'), format_error(result)
            assert str(obj.id)in result.stdout.decode(encoding='utf-8'), format_error(result)
