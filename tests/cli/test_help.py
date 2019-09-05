import pytest

from tests.cli.utils import format_error


class HelpTextError(AssertionError):
    pass


class HelpText(object):
    def __init__(self, result):
        self.stdout = result.stdout.split('\n')
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
    # create
    ('users', 'create', ['--username', '--password'], 'required'),
    ('organizations', 'create', ['--name'], 'required'),
    ('projects', 'create', ['--name'], 'required'),
    ('teams', 'create', ['--name', '--organization'], 'required'),
    ('credentials', 'create', ['--name', '--credential_type'], 'required'),
    ('credential_types', 'create', ['--name', '--kind'], 'required'),
    ('applications', 'create', ['--name', '--client_type',
                                '--authorization_grant_type', '--organization'], 'required'),
    ('tokens', 'create', [], 'required'),
    ('inventory', 'create', ['--name', '--organization'], 'required'),
    ('inventory_scripts', 'create', ['--name', '--organization', '--script'], 'required'),
    ('inventory_sources', 'create', ['--name', '--inventory'], 'required'),
    ('groups', 'create', ['--name', '--inventory'], 'required'),
    ('hosts', 'create', ['--name', '--inventory'], 'required'),
    ('job_templates', 'create', ['--name', '--project', '--playbook'], 'required'),
    ('ad_hoc_commands', 'create', ['--inventory', '--credential'], 'required'),
    ('schedules', 'create', ['--rrule', '--name', '--unified_job_template'], 'required'),
    ('notification_templates', 'create', ['--name', '--organization', '--notification_type'], 'required'),
    ('labels', 'create', ['--name', '--organization'], 'required'),
    ('workflow_job_templates', 'create', ['--name'], 'required'),
    ('workflow_job_template_nodes', 'create', ['--workflow_job_template'], 'required'),
    # associate/disassociate
    ('job_templates', 'associate', ['--credential', '--start_notification',
                                    '--success_notification',
                                    '--failure_notification'], 'optional'),
    ('job_templates', 'disassociate', ['--credential', '--start_notification',
                                       '--success_notification',
                                       '--failure_notification'], 'optional'),
    ('workflow_job_templates', 'associate', ['--start_notification',
                                             '--success_notification',
                                             '--failure_notification'], 'optional'),
    ('workflow_job_templates', 'disassociate', ['--start_notification',
                                                '--success_notification',
                                                '--failure_notification'], 'optional'),
    ('projects', 'associate', ['--start_notification',
                               '--success_notification',
                               '--failure_notification'], 'optional'),
    ('projects', 'disassociate', ['--start_notification',
                                  '--success_notification',
                                  '--failure_notification'], 'optional'),
    ('inventory_sources', 'associate', ['--start_notification',
                                        '--success_notification',
                                        '--failure_notification'], 'optional'),
    ('inventory_sources', 'disassociate', ['--start_notification',
                                           '--success_notification',
                                           '--failure_notification'], 'optional'),
    ('organizations', 'associate', ['--start_notification',
                                    '--success_notification',
                                    '--failure_notification'], 'optional'),
    ('organizations', 'disassociate', ['--start_notification',
                                       '--success_notification',
                                       '--failure_notification'], 'optional'),
]


@pytest.mark.yolo
class TestCLIHelp(object):

    @pytest.mark.parametrize(
        'resource_and_requirements',
        resources_and_requirements,
        ids=[f'{resource[0]}-{resource[1]}' for resource in resources_and_requirements]
        )
    def test_action_specific_help(self, cli, resource_and_requirements):
        # by default, awxkit will use localhost:8043,
        # which shouldn't be reachable in our CI environments
        resource, action, requirements, category = resource_and_requirements
        result = cli(f'awx {resource} {action} --help'.split(), auth=True)
        assert result.returncode in [0, 2], format_error(result)
        help = HelpText(result)
        if requirements:
            errors = []
            if category not in help.parsed:
                errors.append(f"{' '.join(requirements)}")
            else:
                for arg in requirements:
                    if arg not in help.parsed[category]:
                        errors.append(arg)
            if errors:
                raise AssertionError(f'awx {resource} {action} --help is missing {" ".join(errors)} from {category} arguments')
