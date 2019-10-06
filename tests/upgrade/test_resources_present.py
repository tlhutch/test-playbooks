import json
import re

import pytest

from distutils.version import LooseVersion
from awxkit.api.pages.credentials import credential_type_name_to_config_kind_map
from awxkit import config as qe_config


@pytest.mark.usefixtures('authtoken')
class TestResourcesPresent():
    @pytest.fixture(autouse=True)
    def ctid_to_kind(self, v2):
        _ctypes = v2.credential_types.get(managed_by_tower=True, page_size=200).results

        ctypes = _ctypes
        # NOTE(spredzy): Fix properly in 3.5.1. 'external' plugins are new in 3.5.0
        # so they haven't been loaded in pre 3.5.0 (e.g 3.4.3, 3.4.2, ....)
        # so they should not be part of what we check. But we will have to check it
        # for 3.5.0 to 3.5.1, but not for 3.4.3 to 3.5.1
        if LooseVersion(v2.ping.get().version) >= LooseVersion('3.5.0'):
            ctypes = [ctype for ctype in _ctypes if ctype['kind'] != 'external']
        # Same logic applies for 'token' introduced in 3.6.0
        if LooseVersion(v2.ping.get().version) >= LooseVersion('3.6.0'):
            ctypes = [ctype for ctype in _ctypes if ctype['kind'] not in ['token', 'external']]

        ctid_to_name = {ct.id: ct.name.lower() for ct in ctypes}
        name_to_kind = {ct.name.lower(): credential_type_name_to_config_kind_map[ct.name.lower()] for ct in ctypes}

        def _ctid_to_kind(ctid):
            return name_to_kind[ctid_to_name[ctid]].lower()

        return _ctid_to_kind

    def _build_results(self, item, results, *indices):
        keys = [item[index] for index in indices]
        cur = results
        for key in keys[:-1]:
            if key not in cur:
                cur[key] = {}
            cur = cur[key]
        cur[keys[-1]] = item

    def desired_resources(self, resource_type, *indices):
        indices = indices or ('name',)
        results = {}
        for result in qe_config.resources[resource_type]:
            self._build_results(result, results, *indices)
        return results

    @pytest.fixture
    def desired_users(self):
        return self.desired_resources('users', 'username')

    @pytest.fixture
    def desired_organizations(self):
        return self.desired_resources('organizations')

    @pytest.fixture
    def desired_teams(self):
        return self.desired_resources('teams')

    @pytest.fixture
    def desired_credentials(self):
        return self.desired_resources('credentials', 'name', 'kind')

    @pytest.fixture
    def desired_projects(self):
        return self.desired_resources('projects')

    @pytest.fixture
    def desired_inventory_scripts(self):
        return self.desired_resources('inventory_scripts')

    @pytest.fixture
    def desired_inventories(self):
        return self.desired_resources('inventories')

    @pytest.fixture
    def desired_groups(self):
        return self.desired_resources('groups')

    @pytest.fixture
    def desired_inventory_sources(self):
        return self.desired_resources('inventory_sources')

    @pytest.fixture
    def desired_hosts(self):
        return self.desired_resources('hosts')

    @pytest.fixture
    def desired_job_templates(self):
        return self.desired_resources('job_templates')

    def find_resources(self, endpoint, *indices):
        indices = indices or ('name',)
        results = {}
        resources = endpoint.get(order_by=indices[0])
        while True:
            for result in resources.results:
                self._build_results(result, results, *indices)
            if not resources.next:
                return results
            resources = resources.next.get()

    @pytest.fixture
    def found_users(self, v2):
        return self.find_resources(v2.users, 'username')

    @pytest.fixture
    def found_organizations(self, v2):
        return self.find_resources(v2.organizations)

    @pytest.fixture
    def found_teams(self, v2):
        return self.find_resources(v2.teams)

    @pytest.fixture
    def found_credentials(self, v2, ctid_to_kind):
        found_credentials = self.find_resources(v2.credentials, 'name', 'credential_type')
        for found_credential in found_credentials:
            for ctid in list(found_credentials[found_credential]):
                val = found_credentials[found_credential][ctid]
                v2_kind = ctid_to_kind(ctid)
                found_credentials[found_credential][v2_kind] = val
                del found_credentials[found_credential][ctid]
        return found_credentials

    @pytest.fixture
    def found_projects(self, v2):
        return self.find_resources(v2.projects)

    @pytest.fixture
    def found_inventory_scripts(self, v2):
        return self.find_resources(v2.inventory_scripts)

    @pytest.fixture
    def found_inventories(self, v2):
        return self.find_resources(v2.inventory)

    @pytest.fixture
    def found_groups(self, v2):
        # Groups don't have unique names
        found_groups = {}
        for _id, group in self.find_resources(v2.groups, 'id').items():
            if group.name not in found_groups:
                found_groups[group.name] = {}
            found_groups[group.name][_id] = group
        return found_groups

    @pytest.fixture
    def found_inventory_sources(self, v2):
        return self.find_resources(v2.inventory_sources)

    @pytest.fixture
    def found_hosts(self, v2):
        # Hosts don't have unique names
        found_hosts = {}
        for _id, host in self.find_resources(v2.hosts, 'id').items():
            if host.name not in found_hosts:
                found_hosts[host.name] = {}
            found_hosts[host.name][_id] = host
        return found_hosts

    @pytest.fixture
    def found_job_templates(self, v2):
        return self.find_resources(v2.job_templates)

    @pytest.fixture
    def found_jobs(self, v2):
        return self.find_resources(v2.jobs)

    def confirm_field(self, field, found, desired, desired_to_json=False):
        """Determine if the attribute of found matches that of desired"""
        found_attr = getattr(found, field)
        desired_attr = getattr(desired, field)
        if desired_to_json:
            assert json.loads(found_attr) == desired_attr, f"Expected {field} to be {desired_attr} but found {json.loads(found_attr)}"
            return
        assert found_attr == desired_attr, f"Expected {field} to be {desired_attr} but found {found_attr}"

    def confirm_related_field(self, field, found, desired):
        """Determine if the related field name matches that of the desired"""
        desired_value = getattr(desired, field)
        if field == 'credential' and found.type == 'job_template':
            found_value = found.related['credentials'].get().results[0].name
            assert found_value == desired_value, f"Expected {field} to be {desired_value} but found {found_value}"
            return
        found_value = found.related[field].get().name
        if field == 'inventory' and 'local' in found_value:
            # There is a typo in older data sets where "local" is written as "local,"
            found_value = found_value.replace(',', '')
        assert found_value == getattr(desired, field), f"Expected {field} to be {desired_value} but found {found_value}"

    def resolve_duplicates_by_description(self, potential_duplicates, desired_object):
        if len(potential_duplicates) == 1 or 'description' not in desired_object:
            return list(potential_duplicates.values()).pop()

        return [x for x in potential_duplicates.values() if x.description == desired_object.description].pop()

    def test_found_users(self, found_users, desired_users):
        for username, desired_user in desired_users.items():
            found_user = found_users[username]

            # password isn't exposed via the api
            for field in [x for x in desired_user if x != 'password']:
                assert getattr(found_user, field) == getattr(desired_user, field)

    def test_found_organizations(self, found_organizations, desired_organizations):
        for name, desired_organization in desired_organizations.items():
            found_organization = found_organizations[name]
            self.confirm_field('description', found_organization, desired_organization)

            found_org_users = [user.username for user in found_organization.related.users.get().results]
            for user in desired_organization.users:
                assert user in found_org_users

            found_org_admins = [admin.username for admin in found_organization.related.admins.get().results]
            for admin in desired_organization.admins:
                assert admin in found_org_admins

            found_org_projects = [project.name for project in found_organization.related.projects.get().results]
            for project in desired_organization.projects:
                assert project in found_org_projects

    def test_found_teams(self, found_teams, desired_teams):
        for name, desired_team in desired_teams.items():
            found_team = found_teams[name]
            if 'description' in desired_team:
                self.confirm_field('description', found_team, desired_team)

            self.confirm_related_field('organization', found_team, desired_team)

            found_team_users = [user.username for user in found_team.related.users.get().results]
            for user in desired_team.users:
                assert user in found_team_users

    def test_found_credentials(self, found_credentials, desired_credentials):
        for name in desired_credentials:
            for kind, desired_credential in desired_credentials[name].items():
                if isinstance(kind, str):
                    found_credential = found_credentials[name][kind.lower()]
                else:
                    found_credential = found_credentials[name][kind]

                for field in ('description',):
                    self.confirm_field(field, found_credential, desired_credential)

                if desired_credential.user:
                    assert found_credential.related.owner_users.get().results.pop().username == desired_credential.user

                if desired_credential.team:
                    assert found_credential.related.owner_teams.get().results.pop().name == desired_credential.team

    def test_found_projects(self, found_projects, desired_projects):
        projects_to_update = []
        for name, desired_project in desired_projects.items():
            found_project = found_projects[name]
            for field in [x for x in desired_project if x != 'name']:
                if field in ('organization', 'credential'):
                    self.confirm_related_field(field, found_project, desired_project)
                else:
                    # Due to an issue in previous version, when a project was defined with an empty
                    # description, it would be filled with random data making this test fail.
                    if field == 'description' and desired_project[field] == '':
                        continue
                    self.confirm_field(field, found_project, desired_project)
            projects_to_update.append(found_project)

        project_updates = []
        for project in projects_to_update:
            project_updates.append(project.update())

        for update in project_updates:
            update.wait_until_completed(timeout=300, interval=30)
            if not update.is_successful:
                update.get()
                if '429 Too Many Requests' not in update.result_stdout:  # GH rate limit
                    assert update.is_successful, update.result_stdout

    def test_found_inventory_scripts(self, found_inventory_scripts, desired_inventory_scripts):
        for name, desired_script in desired_inventory_scripts.items():
            found_script = found_inventory_scripts[name].get()
            for field in [x for x in desired_script if x not in ['name', 'script']]:
                if field in ('organization',):
                    self.confirm_related_field(field, found_script, desired_script)
                else:
                    self.confirm_field(field, found_script, desired_script)

    def test_found_inventories(self, found_inventories, desired_inventories):
        for name, desired_inventory in desired_inventories.items():
            try:
                found_inventory = found_inventories[name]
            except KeyError:
                if 'azure' in name.lower():
                    # currently we have been always skipping azure, so not going to focus on fixing that right now
                    continue
                if 'local' in name.lower():
                    # There is a typo in older data sets where "local" is written as "local,"
                    found_inventory = found_inventories['local,']
                else:
                    raise

            for field in [x for x in desired_inventory if x != 'name']:
                if field in ('organization',):
                    self.confirm_related_field(field, found_inventory, desired_inventory)
                else:
                    self.confirm_field(field, found_inventory, desired_inventory)

    def test_found_groups(self, found_groups, desired_groups):
        for name, desired_group in desired_groups.items():
            try:
                found_group = self.resolve_duplicates_by_description(found_groups[name], desired_group)
            except KeyError:
                if 'azure' in name.lower():
                    # currently we have been always skipping azure, so not going to focus on fixing that right now
                    continue
                else:
                    raise
            self.confirm_related_field('inventory', found_group, desired_group)
            if 'parent' in desired_group:
                assert found_group.get_parents().pop().name == desired_group.parent

    def test_found_hosts(self, found_hosts, desired_hosts):
        for name, desired_host in desired_hosts.items():
            found_host = self.resolve_duplicates_by_description(found_hosts[name], desired_host)
            for field in [x for x in desired_host if x not in ('name', 'description')]:
                if field == 'inventory':
                    self.confirm_related_field('inventory', found_host, desired_host)
                elif field == 'groups':
                    found_group_names = [group.name for group in found_host.related.groups.get().results]
                    for group in desired_host.groups:
                        assert group in found_group_names
                else:
                    self.confirm_field(field, found_host, desired_host)

    def test_found_inventory_sources(self, found_inventory_sources, found_inventory_scripts, desired_inventory_sources):
        inventory_sources_to_update = []
        for name, desired_inventory_source in desired_inventory_sources.items():
            try:
                found_inventory_source = found_inventory_sources[desired_inventory_source.name]
            except KeyError:
                try:  # We need to filter by what the inventory source will likely be named in tower for implicit inv srcs
                    internal_name = re.compile(r'^{0} \({1}'.format(desired_inventory_source.group,
                                                                   desired_inventory_source.name.split('/')[0]))
                    source_name = [x for x in found_inventory_sources if internal_name.match(x)][0]
                    found_inventory_source = found_inventory_sources[source_name]
                except IndexError:
                    if 'azure' in desired_inventory_source.name.lower():
                        # currently we have been always skipping azure, so not going to focus on fixing that right now
                        continue
                    else:
                        raise
            inclusion = ('credential', 'inventory')
            exclusion = ('update_interval', 'name', 'group')
            for field in [x for x in desired_inventory_source if x not in exclusion]:
                if field in inclusion:
                    self.confirm_related_field(field, found_inventory_source, desired_inventory_source)
                elif field == 'source_script':
                    desired_script_id = found_inventory_scripts[desired_inventory_source.source_script].id
                    assert found_inventory_source.source_script == desired_script_id
                else:
                    self.confirm_field(field, found_inventory_source, desired_inventory_source, field == 'source_vars')
            inventory_sources_to_update.append(found_inventory_source)

        source_updates = []
        for source in inventory_sources_to_update:
            source_updates.append(source.update())

        for update in source_updates:
            update.wait_until_completed(timeout=1200, interval=30)
            if update.source != 'vmware':  # Currently without vmware infra
                assert update.is_successful

    def test_found_job_templates(self, found_job_templates, desired_job_templates):
        job_templates_to_check = []
        for name, desired_job_template in desired_job_templates.items():
            found_job_template = found_job_templates[name]
            for field in [x for x in desired_job_template if x != 'name']:
                if field in ('credential', 'group', 'inventory', 'project'):
                    self.confirm_related_field(field, found_job_template, desired_job_template)
                elif field == 'playbook' and desired_job_template.playbook == 'Default':
                    assert found_job_template.playbook == ''
                else:
                    self.confirm_field(field, found_job_template, desired_job_template, field == 'extra_vars')
            job_templates_to_check.append(found_job_template)

        jobs = []
        for job_template in job_templates_to_check:
            jobs.append(job_template.launch())

        for job in jobs:
            job.wait_until_completed(timeout=1800, interval=30)
            job.get()

        for job in jobs:
            if job.name in ('language_features/tags.yml (tags:foo, limit:unresolvable-name.example.com)',
                            'ansible-playbooks.git/dynamic_inventory.yml',
                            'ansible-tower.git/setup/install.yml'):
                assert job.status == 'failed'
                assert job.job_explanation == ''
            else:
                assert job.is_successful

    def test_ig_mapping(self, v2):
        # Verify IG rebuild mapping
        all_orgs = v2.organizations.get().results
        for org in all_orgs:
            if org['name'].startswith('igmapping Org - '):
                assert org['name'][16:] == \
                    v2.organizations.get(id=org['id']).results.pop().get_related('instance_groups').results.pop().name

        all_jts = v2.job_templates.get().results
        for jt in all_jts:
            if jt['name'].startswith('igmapping JT - '):
                assert jt['name'][15:] == \
                    v2.job_templates.get(id=jt['id']).results.pop().get_related('instance_groups').results.pop().name

        all_invs = v2.inventory.get().results
        for inv in all_invs:
            if inv['name'].startswith('igmapping Inventory - '):
                assert inv['name'][22:] == \
                    v2.inventory.get(id=inv['id']).results.pop().get_related('instance_groups').results.pop().name
