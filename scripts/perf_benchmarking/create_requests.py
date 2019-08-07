#!/usr/bin/env python

from datetime import datetime, timedelta
from itertools import cycle
import logging
import types
import json
import sys

from awxkit import api, utils
from awxkit import exceptions as exc

from .benchmarking import (delete_all_created, no_op, write_results, get_all,  # noqa
                          determine_execution_node_counts, determine_job_event_count)  # noqa


logging.basicConfig(level='DEBUG')
log = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel('DEBUG')
log.addHandler(handler)

# NOTE: Tower is assumed to be licensed before this script runs
v2 = api.ApiV2().load_default_authtoken().get()


org = v2.organizations.create('org')
org_creation_time = org.last_elapsed
write_results(org_creation_time, operation='create organization',
              user='admin', endpoint=str(v2.organizations), method='post')

users = [v2.users.create('user_{0}'.format(i)) for i in range(20)]
user_creation_times = [user.last_elapsed for user in users]
write_results(*user_creation_times, operation='create user',
              user='admin', endpoint=str(v2.users), method='post')

org_association_times = []
for user in users:
    try:
        t0 = datetime.now()
        org.related.users.post(user.json)
    except exc.NoContent:
        pass
    org_association_times.append(datetime.now() - t0)

write_results(*org_association_times, operation='add user to org',
              user='admin', endpoint=str(org.related.users), method='post')

teams = [v2.teams.create('team_{0}'.format(i),
                         organization=org) for i in range(5)]
team_creation_times = [team.last_elapsed for team in teams]
write_results(*team_creation_times, operation='create a team', user='admin',
              endpoint=str(v2.teams), method='post')

for team in teams:
    team_association_times = []
    for user in users:
        try:
            t0 = datetime.now()
            added = team.related.users.post(user.json)
        except exc.NoContent:
            pass
        team_association_times.append(datetime.now() - t0)
    write_results(*team_association_times, operation='add user to team', user='admin',
                  endpoint=str(team.related.users), method='post')


cloud_cred = v2.credentials.create(name='cloud_cred',
                                   kind='aws',
                                   organization=org)
cloud_cred_creation_time = cloud_cred.last_elapsed
write_results(cloud_cred_creation_time, operation='create a cloud cred', user='admin',
              endpoint=str(v2.credentials), method='post')

key_data = open("authorized_key_material", encoding='utf-8').read()  # TODO: obtain via arg
machine_cred = v2.credentials.create(name='machine_cred', kind='ssh',
                                     ssh_key_data=key_data,
                                     organization=org,
                                     become_password='',
                                     password='',
                                     vault_password='')
machine_cred_creation_time = machine_cred.last_elapsed
write_results(machine_cred_creation_time, operation='create a machine cred', user='admin',
              endpoint=str(v2.credentials), method='post')
machine_cred.username = 'centos'


inventories = []
inventory_source_updates = []
inventory_creation_times = []
group_creation_times = []
for i in range(100):
    inv = v2.inventory.create('inv_{}'.format(i), organization=org)
    inventories.append(inv)
    inventory_creation_times.append(inv.last_elapsed)
    group = v2.groups.create('cloud_group_{0}'.format(i), source='ec2',
                             inventory=inv, credential=cloud_cred)
    group_creation_times.append(group.last_elapsed)
    inv_source = group.related.inventory_source.get()
    inventory_source_updates.append(inv_source.update())
write_results(*inventory_creation_times, operation='create an inventory', user='admin',
              endpoint=str(v2.inventory), method='post')
write_results(*group_creation_times, operation='create a group', user='admin',
              endpoint=str(v2.groups), method='post')

for inventory_source_update in inventory_source_updates:
    inventory_source_update.wait_until_completed()


projects = []
project_creation_times = []
for i in range(100):
    project = v2.projects.create(name='project_{}'.format(i),
                                 organization=org, wait=False)
    project_creation_times.append(project.last_elapsed)
    projects.append(project)
write_results(*project_creation_times, operation='create a project', user='admin',
              endpoint=str(v2.projects), method='post')

for project in projects:
    project.related.current_update.get().wait_until_completed()

job_templates = []
job_template_creation_times = []
job_template_limit_setting_times = []
job_template_extra_vars_setting_times = []
job_template_forks_setting_times = []
for i, inv, project in zip(range(100), cycle(inventories), cycle(projects)):
    print(i, inv.name, project.name)
    job_template = v2.job_templates.create('job_template_{0}'.format(i),
                                           playbook='run_shell.yml',
                                           project=project,
                                           credential=machine_cred,
                                           inventory=inv)
    job_template_creation_times.append(job_template.last_elapsed)
    job_template.limit = 'security_group_qe_performance'
    job_template_limit_setting_times.append(job_template.last_elapsed)
    job_template.extra_vars = json.dumps(dict(shell='echo {0}'.format(i),
                                              validate_certs=False))
    job_template_extra_vars_setting_times.append(job_template.last_elapsed)
    job_template.forks = 10
    job_template_forks_setting_times.append(job_template.last_elapsed)
    job_templates.append(job_template)
write_results(*job_template_creation_times, operation='create a job template',
              user='admin', endpoint=str(v2.job_templates), method='post')

job_launching_t0 = datetime.now()
job_launch_times = []
i = 1
for _ in range(20):
    launch_list = []
    for job_template in job_templates:
        try:
            launched = job_template.related.launch.post()
            print(i, 'job id: ', launched.id)
        except exc.Unauthorized:
            v2.load_default_authtoken().get()
            launched = job_template.related.launch.post()
            print(i, 'job id: ', launched.id)
        except Exception as e:
            print(e)
            launched = utils.PseudoNamespace()
            launched.last_elapsed = timedelta(0)
            launched.wait_until_completed = types.MethodType(no_op, launched)

        if isinstance(launched, api.JobTemplateLaunch):
            launched = api.Job(launched.connection, endpoint=launched.endpoint,
                               last_elapsed=launched.last_elapsed)

        job_launch_times.append(launched.last_elapsed)
        launch_list.append(launched)
        i += 1
        write_results(launched.last_elapsed, operation='launch a job template',
                      user='admin', endpoint=str(job_template.related.launch), method='post')

    for job in launch_list:
        job.get()
        job.wait_until_completed(timeout=6000)

job_launching_clock_time = datetime.now() - job_launching_t0
write_results(job_launching_clock_time, operation='launch and run 2000 jobs',
              user='admin', endpoint='na', method='na')
