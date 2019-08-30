import pytest

from tests.cli.utils import format_error


resources_and_roles = [
        ('organization', [
            'notification_admin',
            'project_admin',
            'workflow_admin',
            'credential_admin',
            'admin',
            'execute',
            'approval',
            'read',
            'job_template_admin',
            'inventory_admin',
            'auditor',
            'member'
            ]),
        ('team', [
            'admin',
            'read',
            'member'
            ]),
        ('project', [
            'admin',
            'update',
            'read',
            'use',
            ]),
        ('inventory', [
            'admin',
            'update',
            'read',
            'adhoc',
            'use',
            ]),
        ('inventory_script', [
            'admin',
            'read',
            ]),
        ('credential', [
            'admin',
            'read',
            'use',
            ]),
        ('job_template', [
            'admin',
            'read',
            'execute',
            ]),
        ('workflow_job_template', [
            'admin',
            'read',
            'execute',
            'approval',
            ]),
        ]


class TestCLIUserRoles(object):

    @pytest.fixture(params=resources_and_roles, ids=[r[0] for r in resources_and_roles])
    def resource_role_and_objects(self, class_factories, request):
        resource, roles = request.param
        everything = {}
        everything['organization'] = org = class_factories.organization()
        everything['team'] = class_factories.team(organization=org)
        if resource in ['inventory', 'inventory_script', 'job_template']:
            everything['inventory_script'] = inventory_script = class_factories.inventory_script(organization=org)
            everything['inventory'] = inventory = class_factories.inventory(script=inventory_script)
        if resource in ['project', 'job_template']:
            everything['project'] = project = class_factories.project(organization=org)
        if resource in ['job_template']:
            everything['job_template'] = class_factories.job_template(organization=org, project=project, inventory=inventory)
        if resource in ['workflow_job_template']:
            everything['workflow_job_template'] = class_factories.workflow_job_template(organization=org)
        if resource in ['credential']:
            everything['credential'] = class_factories.credential(organization=org)
        return resource, roles, everything

    def get_user_roles(self, user):
        return [
            {
               'role': role['name'].lower().replace(' ', '_').replace('approve', 'approval').replace('ad_hoc', 'adhoc'),
               'resource': role['summary_fields']['resource_type'].replace('custom_inventory_script', 'inventory_script')
            } for role in user.related.roles.get().results
            ]

    def test_role_grant_and_revoke(self, cli, factories, resource_role_and_objects):
        user = factories.user()
        resource, roles, connected_resources = resource_role_and_objects
        if resource != 'organization':
            connected_resources['organization'].set_object_roles(user, 'member')
        for role in roles:
            result = cli(f'awx user grant {user.id} --{resource} {connected_resources[resource].id} --type {role}'.split(), auth=True)
            user_roles = self.get_user_roles(user)
            assert role in [user_role['role'] for user_role in user_roles if user_role['resource'] == resource], f'User did not get {role} on {resource}: {user_roles}'
            assert result.returncode == 0, format_error(result)
            result = cli(f'awx user revoke {user.id} --{resource} {connected_resources[resource].id} --type {role}'.split(), auth=True)
            assert result.returncode == 0, format_error(result)
            user_roles = self.get_user_roles(user)
            assert role not in [user_role['role'] for user_role in user_roles if user_role['resource'] == resource], f'User still has {role} on {resource}: {user_roles}'
