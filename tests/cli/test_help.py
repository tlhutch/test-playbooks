import pytest

from tests.cli.utils import format_error


class HelpTextError(AssertionError):
    pass


class HelpText(object):
    def __init__(self, result):
        self.stdout = result.stdout.decode(encoding='utf-8').split('\n')
        self.parsed = {'unknown': ''}
        key = 'unknown'
        for line in self.stdout:
            if line.startswith('usage:'):
                key = 'usage'
                if key in self.parsed:
                    raise HelpTextError(f'found multiple "{key}" sections of help text.')
                self.parsed[key] = line
            elif line.startswith('optional arguments:'):
                key = 'optional'
                if key in self.parsed:
                    raise HelpTextError(f'found multiple "{key}" sections of help text.')
                self.parsed[key] = line
                continue
            elif line.startswith('required arguments:'):
                key = 'required'
                if key in self.parsed:
                    raise HelpTextError(f'found multiple "{key}" sections of help text.')
                self.parsed[key] = line
            elif line.startswith('positional arguments:'):
                key = 'positional'
                if key in self.parsed:
                    raise HelpTextError(f'found multiple "{key}" sections of help text.')
                self.parsed[key] = line
            elif line.startswith('authentication:'):
                key = 'authentication'
                if key in self.parsed:
                    raise HelpTextError(f'found multiple "{key}" sections of help text.')
                self.parsed[key] = line
            elif line.startswith('output formatting:'):
                key = 'output'
                if key in self.parsed:
                    raise HelpTextError(f'found multiple "{key}" sections of help text.')
                self.parsed[key] = line
            elif line.startswith('awx'):
                key = 'final'
                if key in self.parsed:
                    raise HelpTextError(f'found multiple "{key} <resource> ..." sections of help text.')
                self.parsed[key] = line
            elif line == '\n':
                key = 'unknown'
            else:
                self.parsed[key] = self.parsed[key] + line


resources_and_requirements = [
        ('users', ['--username', '--password']),
        ('organizations', ['--name']),
        ('projects', ['--name']),
        ('teams', ['--name', '--organization']),
        ('credentials', ['--name', '--credential_type']),
        ('credential_types', ['--name', '--kind']),
        ('applications', ['--name', '--client_type', '--authorization_grant_type', '--organization']),
        ('tokens', []),
        ('inventory', ['--name', '--organization']),
        ('inventory_scripts', ['--name', '--organization', '--script']),
        ('inventory_sources', ['--name', '--inventory']),
        ('groups', ['--name', '--inventory']),
        ('hosts', ['--name', '--inventory']),
        ('job_templates', ['--name', '--project', '--playbook']),
        ('ad_hoc_commands', ['--inventory', '--credential']),
        ('schedules', ['--rrule', '--name', '--unified_job_template']),
        ('notification_templates', ['--name', '--organization', '--notification_type']),
        ('labels', ['--name', '--organization']),
        ('workflow_job_templates', ['--name']),
        ('workflow_job_template_nodes', ['--workflow_job_template']),
        ]


@pytest.mark.yolo
class TestCLIHelp(object):

    @pytest.mark.parametrize(
        'resource_and_requirements',
        resources_and_requirements,
        ids=[resource[0] for resource in resources_and_requirements]
        )
    def test_create_help(self, cli, resource_and_requirements):
        # by default, awxkit will use localhost:8043,
        # which shouldn't be reachable in our CI environments
        resource, requirements = resource_and_requirements
        result = cli(f'awx {resource} create --help'.split(), auth=True)
        assert result.returncode in [0, 2], format_error(result)
        help = HelpText(result)
        if requirements:
            errors = []
            if 'required' not in help.parsed:
                errors.append(f"{' '.join(requirements)}")
            else:
                for arg in requirements:
                    if arg not in help.parsed['required']:
                        errors.append(arg)
            if errors:
                raise AssertionError(f'awx {resource} create --help is missing {" ".join(errors)} from required arguments')
