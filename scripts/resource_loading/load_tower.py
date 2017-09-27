#!/usr/bin/env python

import logging
import json
import sys

from towerkit import api, config, exceptions, utils

from loading import resources, delete_all_created  # noqa


logging.basicConfig(level='DEBUG')
log = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel('DEBUG')
log.addHandler(handler)


v1 = api.ApiV1().load_default_authtoken().get()
v1.config.get().install_license()


# Create users
users = {}
for user in resources.users:
    log.info('Creating User: {0.username}'.format(user))
    users[user.username] = v1.users.create(user.username, user.password,
                                           email=user.email,
                                           first_name=user.first_name,
                                           last_name=user.last_name,
                                           is_superuser=user.is_superuser)

# Create organizations
organizations = {}
for organization in resources.organizations:
    log.info('Creating Organization: {0.name}'.format(organization))
    org = v1.organizations.create(organization.name, organization.description)
    organizations[organization.name] = org
    for username in organization.users:
        org.add_user(users[username])
    for username in organization.admins:
        org.add_admin(users[username])

# Create teams
teams = {}
for team in resources.teams:
    log.info('Creating Team: {0.name}'.format(team))
    created_team = v1.teams.create(team.name, description=team.get('description', ''),
                                   organization=organizations[team.organization])
    teams[team.name] = created_team
    for username in team.users:
        with utils.suppress(exceptions.NoContent):
            created_team.related.users.post(users[username].json)

# Create credentials
credentials = {}
for credential in resources.credentials:
    log.info('Creating Credential: {0.name}'.format(credential))
    for item, source in (('user', users), ('team', teams)):
        found = credential.get(item, False)
        if found:
            credential[item] = source[found]

    if credential.kind in utils.cloud_types:
        if credential.kind == 'azure':
            config_credential = config.credentials.cloud.azure_classic
        else:
            config_credential = config.credentials.cloud[credential.kind]
    else:
        config_credential = config.credentials[credential.kind]

    for field in filter(lambda x: x in credential, config_credential):
        value = credential[field].format(**config_credential)
        credential[field] = value

    if 'project' in credential:
        credential['project_id' if credential.kind == 'gce' else 'project_name'] = credential.pop('project')

    credentials[credential.name] = v1.credentials.create(**credential)

# Create projects
projects = {}
project_updates = []
for project in resources.projects:
    log.info('Creating Project: {0.name}'.format(project))
    project['organization'] = organizations[project['organization']]
    if 'credential' in project:
        project['credential'] = credentials[project['credential']]
    projects[project.name] = v1.projects.create(wait=False, **project)
    project_updates.append(projects[project.name].related.current_update.get())

for update in project_updates:
    update.wait_until_completed(timeout=300, interval=30)

for update in project_updates:
    assert update.is_successful

# Create inventory scripts
inventory_scripts = {}
for inventory_script in resources.inventory_scripts:
    log.info('Creating Inventory Script: {0.name}'.format(inventory_script))
    inv_script = v1.inventory_scripts.create(inventory_script.name, inventory_script.description,
                                             organization=organizations[inventory_script.organization],
                                             script=inventory_script.script)
    inventory_scripts[inventory_script.name] = inv_script

# Create inventories
inventories = {}
for inventory in resources.inventories:
    log.info('Creating Inventory: {0.name}'.format(inventory))
    inventory['organization'] = organizations[inventory.organization]
    if 'variables' in inventory:
        inventory['variables'] = json.dumps(inventory['variables'])
    inventories[inventory.name] = v1.inventory.create(**inventory)

# Create groups
groups = {}
for group in resources.groups:
    log.info('Creating Group: {0.name}'.format(group))
    group['inventory'] = inventories[group.inventory]
    if 'variables' in group:
        group['variables'] = json.dumps(group['variables'])
    if 'parent' in group:
        group['parent'] = groups[group['parent']]
    groups[group.name] = v1.groups.create(**group)

# Create hosts
hosts = {}
for host in resources.hosts:
    log.info('Creating Host: {0.name}'.format(host))
    _groups = host.pop('groups', ())
    if 'variables' in host:
        host['variables'] = json.dumps(host['variables'])
    host['inventory'] = inventories[host.inventory]
    hosts[host.name] = v1.hosts.create(**host)
    for group in _groups:
        groups[group].add_host(hosts[host.name])

# Create inventory sources
inventory_sources = {}
inventory_source_updates = []
for inventory_source in resources.inventory_sources:
    log.info('Creating Inventory Source: {0.name}'.format(inventory_source))
    group = groups[inventory_source.pop('group')]
    if 'source_vars' in inventory_source:
        inventory_source['source_vars'] = json.dumps(inventory_source['source_vars'])
    for field, store in (('credential', credentials), ('source_script', inventory_scripts)):
        if field in inventory_source:
            inventory_source[field] = store[inventory_source[field]].id
    created_inventory_source = group.related.inventory_source.patch(**inventory_source)
    inventory_sources[inventory_source.name] = created_inventory_source
    inventory_source_updates.append(created_inventory_source.update())

for update in inventory_source_updates:
    update.wait_until_completed(timeout=1200, interval=30)

# for update in inventory_source_updates:
#     assert update.is_successful

# Create job templates
job_templates = {}
for job_template in resources.job_templates:
    log.info('Creating Job Template: {0.name}'.format(job_template))
    jt_args = {field: job_template[field] for field in job_template}
    for item, source in (('project', projects),
                         ('inventory', inventories),
                         ('credential', credentials)):
        found = jt_args.get(item, False)
        if found:
            jt_args[item] = source[found]

    if 'extra_vars' in job_template:
        jt_args['extra_vars'] = json.dumps(job_template.extra_vars)

    jt = v1.job_templates.create(**jt_args)

    job_templates[job_template.name] = jt

jobs = []
for jt in job_templates.values():
    jobs.append(jt.launch())

for job in jobs:
    job.wait_until_completed(timeout=1800, interval=30)

for job in jobs:
    try:
        if job.name in ('ansible-playbooks.git/dynamic_inventory.yml',
                        'ansible-tower.git/setup/install.yml'):
            assert job.status == 'failed'
            assert job.job_explanation == ''
        else:
            assert job.is_successful
    except Exception as e:
        log.exception(e)
