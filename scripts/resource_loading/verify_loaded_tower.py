#!/usr/bin/env python

import logging
import json
import sys

from towerkit import api

from loading import resources, delete_all_created  # noqa


logging.basicConfig(level='DEBUG')
log = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel('DEBUG')
log.addHandler(handler)


v1 = api.ApiV1().load_default_authtoken().get()


def desired_resources(resource_type, identifier='name'):
    return {item[identifier]: item for item in resources[resource_type]}


desired_users = desired_resources('users', 'username')
desired_organizations = desired_resources('organizations')
desired_teams = desired_resources('teams')
desired_credentials = desired_resources('credentials')
desired_projects = desired_resources('projects')
desired_inventory_scripts = desired_resources('inventory_scripts')
desired_inventories = desired_resources('inventories')
desired_groups = desired_resources('groups')
desired_inventory_sources = desired_resources('inventory_sources')
desired_hosts = desired_resources('hosts')
desired_job_templates = desired_resources('job_templates')


def find_resources(endpoint, identifier='name'):
    results = {}
    resources = endpoint.get(order_by=identifier)
    while True:
        results.update({item[identifier]: item for item in resources.results})
        if not resources.next:
            return results
        resources = resources.next.get()


found_users = find_resources(v1.users, 'username')
found_organizations = find_resources(v1.organizations)
found_teams = find_resources(v1.teams)
found_credentials = find_resources(v1.credentials)
found_projects = find_resources(v1.projects)
found_inventory_scripts = find_resources(v1.inventory_scripts)
found_inventories = find_resources(v1.inventory)

# Groups don't have unique names
found_groups = {}
for _id, group in find_resources(v1.groups, 'id').items():
    if group.name not in found_groups:
        found_groups[group.name] = {}
    found_groups[group.name][_id] = group

found_inventory_sources = find_resources(v1.inventory_sources)

# Hosts don't have unique names
found_hosts = {}
for _id, host in find_resources(v1.hosts, 'id').items():
    if host.name not in found_hosts:
        found_hosts[host.name] = {}
    found_hosts[host.name][_id] = host

found_job_templates = find_resources(v1.job_templates)
found_jobs = find_resources(v1.jobs)


def confirm_field(field, found, desired, desired_to_json=False):
    """Determine if the attribute of found matches that of desired"""
    found_attr = getattr(found, field)
    desired_attr = getattr(desired, field)
    if desired_to_json:
        return found_attr == json.dumps(desired_attr)
    return found_attr == desired_attr


def confirm_related_field(field, found, desired):
    """Determine if the related field name matches that of the desired"""
    return found.related[field].get().name == getattr(desired, field)


def resolve_duplicates_by_description(potential_duplicates, desired_object):
    if len(potential_duplicates) == 1 or 'description' not in desired_object:
        return potential_duplicates.values().pop()

    return filter(lambda x: x.description == desired_object.description,
                  potential_duplicates.values()).pop()


log.info('Verifying users')
for username, desired_user in desired_users.items():
    found_user = found_users[username]

    # password isn't exposed via the api
    for field in filter(lambda x: x != 'password', desired_user):
        assert(getattr(found_user, field) == getattr(desired_user, field))

log.info('Verifying organizations')
for name, desired_organization in desired_organizations.items():
    found_organization = found_organizations[name]
    assert(confirm_field('description', found_organization, desired_organization))

    found_org_users = [user.username for user in found_organization.related.users.get().results]
    for user in desired_organization.users:
        assert(user in found_org_users)

    found_org_admins = [admin.username for admin in found_organization.related.admins.get().results]
    for admin in desired_organization.admins:
        assert(admin in found_org_admins)

    found_org_projects = [project.name for project in found_organization.related.projects.get().results]
    for project in desired_organization.projects:
        assert(project in found_org_projects)

log.info('Verifying teams')
for name, desired_team in desired_teams.items():
    found_team = found_teams[name]
    if 'description' in desired_team:
        assert(confirm_field('description', found_team, desired_team))

    assert(confirm_related_field('organization', found_team, desired_team))

    found_team_users = [user.username for user in found_team.related.users.get().results]
    for user in desired_team.users:
        assert(user in found_team_users)

log.info('Verifying credentials')
# note: content validity determined by successful updates of credential usage
for name, desired_credential in desired_credentials.items():
    found_credential = found_credentials[name]
    for field in ('kind', 'description'):
        assert(confirm_field(field, found_credential, desired_credential))

    if desired_credential.user:
        assert(found_credential.related.owner_users.get().results.pop().username == desired_credential.user)

    if desired_credential.team:
        assert(found_credential.related.owner_teams.get().results.pop().name == desired_credential.team)

log.info('Verifying projects')
projects_to_update = []
for name, desired_project in desired_projects.items():
    found_project = found_projects[name]
    for field in filter(lambda x: x != 'name', desired_project):
        if field in ('organization', 'credential'):
            assert(confirm_related_field(field, found_project, desired_project))
        else:
            assert(confirm_field(field, found_project, desired_project))
    projects_to_update.append(found_project)

log.info('Verifying inventory scripts')
for name, desired_script in desired_inventory_scripts.items():
    found_script = found_inventory_scripts[name]
    for field in filter(lambda x: x != 'name', desired_script):
        if field in ('organization',):
            assert(confirm_related_field(field, found_script, desired_script))
        else:
            assert(confirm_field(field, found_script, desired_script))

log.info('Verifying inventories')
for name, desired_inventory in desired_inventories.items():
    found_inventory = found_inventories[name]
    for field in filter(lambda x: x != 'name', desired_inventory):
        if field in ('organization',):
            assert(confirm_related_field(field, found_inventory, desired_inventory))
        else:
            assert(confirm_field(field, found_inventory, desired_inventory, field == 'variables'))

log.info('Verifying groups')
for name, desired_group in desired_groups.items():
    found_group = resolve_duplicates_by_description(found_groups[name], desired_group)
    assert(confirm_related_field('inventory', found_group, desired_group))
    if 'parent' in desired_group:
        assert(found_group.get_parents().pop().name == desired_group.parent)

log.info('Verifying hosts')
for name, desired_host in desired_hosts.items():
    found_host = resolve_duplicates_by_description(found_hosts[name], desired_host)
    for field in filter(lambda x: x not in ('name', 'description'), desired_host):
        if field == 'inventory':
            assert(confirm_related_field('inventory', found_host, desired_host))
        elif field == 'groups':
            found_group_names = [group.name for group in found_host.related.groups.get().results]
            for group in desired_host.groups:
                assert(group in found_group_names)
        else:
            assert(confirm_field(field, found_host, desired_host, field == 'variables'))

log.info('Verifying inventory sources')
inventory_sources_to_update = []
for name, desired_inventory_source in desired_inventory_sources.items():
    # We need to filter by what the inventory source will likely be named in tower
    internal_name = '{0} ({1}'.format(desired_inventory_source.group,
                                      desired_inventory_source.name.split('/')[0])
    source_name = filter(lambda x: internal_name in x, found_inventory_sources).pop()
    found_inventory_source = found_inventory_sources[source_name]
    for field in filter(lambda x: x not in ('update_interval', 'name'),
                        desired_inventory_source):
        if field in ('credential', 'group', 'inventory'):
            assert(confirm_related_field(field, found_inventory_source, desired_inventory_source))
        elif field == 'source_script':
            desired_script_id = found_inventory_scripts[desired_inventory_source.source_script].id
            assert(found_inventory_source.source_script == desired_script_id)
        else:
            assert(confirm_field(field, found_inventory_source, desired_inventory_source, field == 'source_vars'))
    inventory_sources_to_update.append(found_inventory_source)

log.info('Verifying job templates')
job_templates_to_check = []
for name, desired_job_template in desired_job_templates.items():
    found_job_template = found_job_templates[name]
    for field in filter(lambda x: x != 'name', desired_job_template):
        if field in ('credential', 'group', 'inventory', 'project'):
            assert(confirm_related_field(field, found_job_template, desired_job_template))
        elif field == 'playbook' and desired_job_template.playbook == 'Default':
            assert(found_job_template.playbook == '')
        else:
            assert(confirm_field(field, found_job_template, desired_job_template, field == 'extra_vars'))
    job_templates_to_check.append(found_job_template)

log.info('Verifying project updates are successful')
project_updates = []
for project in projects_to_update:
    project_updates.append(project.update())

for update in project_updates:
    update.wait_until_completed(timeout=300, interval=30)
    assert(update.is_successful)

log.info('Verifying updated inventory sources are successful')
source_updates = []
for source in inventory_sources_to_update:
    source_updates.append(source.update())

for update in source_updates:
    update.wait_until_completed(timeout=1200, interval=30)
    assert(update.is_successful)

log.info('Verify job templates can be launched')
jobs = []
for job_template in job_templates_to_check:
    jobs.append(job_template.launch())

for job in jobs:
    job.wait_until_completed(timeout=1800, interval=30)
