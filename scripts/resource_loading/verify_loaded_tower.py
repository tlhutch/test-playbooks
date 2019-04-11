#!/usr/bin/env python

import logging
import json
import sys
import re

from towerkit import api, config
from towerkit.tower.utils import uses_sessions

from .loading import args, resources, delete_all_created  # noqa


logging.basicConfig(level='DEBUG')
log = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel('DEBUG')
log.addHandler(handler)


root = api.Api()
if uses_sessions(root.connection):
    config.use_sessions = True
    root.load_session().get()
else:
    root.load_authtoken().get()
v = root.current_version.get()

use_v2 = 'v2' in root.available_versions

if use_v2:
    from towerkit.api.pages.credentials import credential_type_name_to_config_kind_map
    _ctypes = v.credential_types.get(managed_by_tower=True, page_size=200).results

    # NOTE(spredzy): Fix properly in 3.5.1. 'external' plugins are new in 3.5.0
    # so they haven't been loaded in pre 3.5.0 (e.g 3.4.3, 3.4.2, ....)
    # so they should not be part of what we check. But we will have to check it
    # for 3.5.0 to 3.5.1, but not for 3.4.3 to 3.5.1
    if v.ping.get().version == '3.5.0':
        ctypes = [ctype for ctype in _ctypes if ctype['kind'] != 'external']
    else:
        ctypes = _ctypes

    ctid_to_name = {ct.id: ct.name.lower() for ct in ctypes}
    name_to_kind = {ct.name.lower(): credential_type_name_to_config_kind_map[ct.name.lower()] for ct in ctypes}

    def ctid_to_kind(ctid):
        return name_to_kind[ctid_to_name[ctid]]


def _build_results(item, results, *indices):
    keys = [item[index] for index in indices]
    cur = results
    for key in keys[:-1]:
        if key not in cur:
            cur[key] = {}
        cur = cur[key]
    cur[keys[-1]] = item


def desired_resources(resource_type, *indices):
    indices = indices or ('name',)
    results = {}
    for result in resources[resource_type]:
        _build_results(result, results, *indices)
    return results


desired_users = desired_resources('users', 'username')
desired_organizations = desired_resources('organizations')
desired_teams = desired_resources('teams')
desired_credentials = desired_resources('credentials', 'name', 'kind')
desired_projects = desired_resources('projects')
desired_inventory_scripts = desired_resources('inventory_scripts')
desired_inventories = desired_resources('inventories')
desired_groups = desired_resources('groups')
desired_inventory_sources = desired_resources('inventory_sources')
desired_hosts = desired_resources('hosts')
desired_job_templates = desired_resources('job_templates')


def find_resources(endpoint, *indices):
    indices = indices or ('name',)
    results = {}
    resources = endpoint.get(order_by=indices[0])
    while True:
        for result in resources.results:
            _build_results(result, results, *indices)
        if not resources.next:
            return results
        resources = resources.next.get()


found_users = find_resources(v.users, 'username')
found_organizations = find_resources(v.organizations)
found_teams = find_resources(v.teams)
if use_v2:
    found_credentials = find_resources(v.credentials, 'name', 'credential_type')
    for found_credential in found_credentials:
        for ctid in list(found_credentials[found_credential]):
            val = found_credentials[found_credential][ctid]
            v1_kind = ctid_to_kind(ctid)
            found_credentials[found_credential][v1_kind] = val
            del found_credentials[found_credential][ctid]
else:
    found_credentials = find_resources(v.credentials)
found_projects = find_resources(v.projects)
found_inventory_scripts = find_resources(v.inventory_scripts)
found_inventories = find_resources(v.inventory)

# Groups don't have unique names
found_groups = {}
for _id, group in find_resources(v.groups, 'id').items():
    if group.name not in found_groups:
        found_groups[group.name] = {}
    found_groups[group.name][_id] = group

found_inventory_sources = find_resources(v.inventory_sources)

# Hosts don't have unique names
found_hosts = {}
for _id, host in find_resources(v.hosts, 'id').items():
    if host.name not in found_hosts:
        found_hosts[host.name] = {}
    found_hosts[host.name][_id] = host

found_job_templates = find_resources(v.job_templates)
found_jobs = find_resources(v.jobs)


def confirm_field(field, found, desired, desired_to_json=False):
    """Determine if the attribute of found matches that of desired"""
    found_attr = getattr(found, field)
    desired_attr = getattr(desired, field)
    if desired_to_json:
        return json.loads(found_attr) == desired_attr
    return found_attr == desired_attr


def confirm_related_field(field, found, desired):
    """Determine if the related field name matches that of the desired"""
    return found.related[field].get().name == getattr(desired, field)


def resolve_duplicates_by_description(potential_duplicates, desired_object):
    if len(potential_duplicates) == 1 or 'description' not in desired_object:
        return list(potential_duplicates.values()).pop()

    return [x for x in potential_duplicates.values() if x.description == desired_object.description].pop()


log.info('Verifying users')
for username, desired_user in desired_users.items():
    found_user = found_users[username]

    # password isn't exposed via the api
    for field in [x for x in desired_user if x != 'password']:
        assert getattr(found_user, field) == getattr(desired_user, field)

log.info('Verifying organizations')
for name, desired_organization in desired_organizations.items():
    found_organization = found_organizations[name]
    assert confirm_field('description', found_organization, desired_organization)

    found_org_users = [user.username for user in found_organization.related.users.get().results]
    for user in desired_organization.users:
        assert user in found_org_users

    found_org_admins = [admin.username for admin in found_organization.related.admins.get().results]
    for admin in desired_organization.admins:
        assert admin in found_org_admins

    found_org_projects = [project.name for project in found_organization.related.projects.get().results]
    for project in desired_organization.projects:
        assert project in found_org_projects

log.info('Verifying teams')
for name, desired_team in desired_teams.items():
    found_team = found_teams[name]
    if 'description' in desired_team:
        assert confirm_field('description', found_team, desired_team)

    assert confirm_related_field('organization', found_team, desired_team)

    found_team_users = [user.username for user in found_team.related.users.get().results]
    for user in desired_team.users:
        assert user in found_team_users

log.info('Verifying credentials')
for name in desired_credentials:
    for kind, desired_credential in desired_credentials[name].items():
        if use_v2:
            found_credential = found_credentials[name][kind]
        else:
            found_credential = found_credentials[name]

        for field in ('description',):
            assert confirm_field(field, found_credential, desired_credential)

        if desired_credential.user:
            assert found_credential.related.owner_users.get().results.pop().username == desired_credential.user

        if desired_credential.team:
            assert found_credential.related.owner_teams.get().results.pop().name == desired_credential.team

log.info('Verifying projects')
projects_to_update = []
for name, desired_project in desired_projects.items():
    found_project = found_projects[name]
    for field in [x for x in desired_project if x != 'name']:
        if field in ('organization', 'credential'):
            assert confirm_related_field(field, found_project, desired_project)
        else:
            assert confirm_field(field, found_project, desired_project)
    projects_to_update.append(found_project)

log.info('Verifying inventory scripts')
for name, desired_script in desired_inventory_scripts.items():
    found_script = found_inventory_scripts[name].get()
    for field in [x for x in desired_script if x not in ['name', 'script']]:
        if field in ('organization',):
            assert confirm_related_field(field, found_script, desired_script)
        else:
            assert confirm_field(field, found_script, desired_script)

log.info('Verifying inventories')
for name, desired_inventory in desired_inventories.items():
    try:
        found_inventory = found_inventories[name]
    except KeyError:
        if 'azure' in name.lower() and args.no_azure:
            continue
        else:
            raise

    for field in [x for x in desired_inventory if x != 'name']:
        if field in ('organization',):
            assert confirm_related_field(field, found_inventory, desired_inventory)
        else:
            assert confirm_field(field, found_inventory, desired_inventory)

log.info('Verifying groups')
for name, desired_group in desired_groups.items():
    try:
        found_group = resolve_duplicates_by_description(found_groups[name], desired_group)
    except KeyError:
        if 'azure' in name.lower() and args.no_azure:
            continue
        else:
            raise
    assert confirm_related_field('inventory', found_group, desired_group)
    if 'parent' in desired_group:
        assert found_group.get_parents().pop().name == desired_group.parent

log.info('Verifying hosts')
for name, desired_host in desired_hosts.items():
    found_host = resolve_duplicates_by_description(found_hosts[name], desired_host)
    for field in [x for x in desired_host if x not in ('name', 'description')]:
        if field == 'inventory':
            assert confirm_related_field('inventory', found_host, desired_host)
        elif field == 'groups':
            found_group_names = [group.name for group in found_host.related.groups.get().results]
            for group in desired_host.groups:
                assert group in found_group_names
        else:
            assert confirm_field(field, found_host, desired_host)

log.info('Verifying inventory sources')
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
            if 'azure' in desired_inventory_source.name.lower() and args.no_azure:
                continue
            else:
                raise
    if use_v2:
        inclusion = ('credential', 'inventory')
        exclusion = ('update_interval', 'name', 'group')
    else:
        inclusion = ('credential', 'inventory', 'group')
        exclusion = ('update_interval', 'name')
    for field in [x for x in desired_inventory_source if x not in exclusion]:
        if field in inclusion:
            assert confirm_related_field(field, found_inventory_source, desired_inventory_source)
        elif field == 'source_script':
            desired_script_id = found_inventory_scripts[desired_inventory_source.source_script].id
            assert found_inventory_source.source_script == desired_script_id
        else:
            assert confirm_field(field, found_inventory_source, desired_inventory_source, field == 'source_vars')
    inventory_sources_to_update.append(found_inventory_source)

log.info('Verifying job templates')
job_templates_to_check = []
for name, desired_job_template in desired_job_templates.items():
    found_job_template = found_job_templates[name]
    for field in [x for x in desired_job_template if x != 'name']:
        if field in ('credential', 'group', 'inventory', 'project'):
            assert confirm_related_field(field, found_job_template, desired_job_template)
        elif field == 'playbook' and desired_job_template.playbook == 'Default':
            assert found_job_template.playbook == ''
        else:
            assert confirm_field(field, found_job_template, desired_job_template, field == 'extra_vars')
    job_templates_to_check.append(found_job_template)

log.info('Verifying project updates are successful')
project_updates = []
for project in projects_to_update:
    project_updates.append(project.update())

for update in project_updates:
    update.wait_until_completed(timeout=300, interval=30)
    if not update.is_successful:
        update.get()
        if '429 Too Many Requests' not in update.result_stdout:  # GH rate limit
            assert update.is_successful, update.result_stdout

log.info('Verifying updated inventory sources are successful')
source_updates = []
for source in inventory_sources_to_update:
    source_updates.append(source.update())

for update in source_updates:
    update.wait_until_completed(timeout=1200, interval=30)
    if update.source != 'vmware':  # Currently without vmware infra
        assert update.is_successful

log.info('Verify job templates can be launched')
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

# Verify IG rebuild mapping
log.info('Verify IG rebuild mapping')
all_orgs = v.organizations.get().results
for org in all_orgs:
    if org['name'].startswith('igmapping Org - '):
        assert org['name'][16:] == \
            v.organizations.get(id=org['id']).results.pop().get_related('instance_groups').results.pop().name

all_jts = v.job_templates.get().results
for jt in all_jts:
    if jt['name'].startswith('igmapping JT - '):
        assert jt['name'][15:] == \
            v.job_templates.get(id=jt['id']).results.pop().get_related('instance_groups').results.pop().name

all_invs = v.inventory.get().results
for inv in all_invs:
    if inv['name'].startswith('igmapping Inventory - '):
        assert inv['name'][22:] == \
            v.inventory.get(id=inv['id']).results.pop().get_related('instance_groups').results.pop().name
