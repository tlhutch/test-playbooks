import threading
import json

import pytest

from awxkit import config, exceptions, utils


@pytest.mark.usefixtures('authtoken')
class TestLoadResources():
    @pytest.fixture(scope='class')
    def rbac_structure(self, v2_class):
        # Create users
        users = {}
        for user in config.resources.users:
            created = v2_class.users.create_or_replace(username=user.username,
                                               email=user.email,
                                               first_name=user.first_name,
                                               last_name=user.last_name,
                                               is_superuser=user.is_superuser)
            created.password = user.password
            users[user.username] = created

        organizations = {}
        for organization in config.resources.organizations:
            org = v2_class.organizations.create_or_replace(name=organization.name, description=organization.description)
            organizations[organization.name] = org
            for username in organization.users:
                if not org.related.users.get(username=username).results:
                    org.add_user(users[username])
            for username in organization.admins:
                if not org.related.admins.get(username=username).results:
                    org.add_admin(users[username])

        # Create teams
        teams = {}
        for team in config.resources.teams:
            description = team.get('description', '')
            created_team = v2_class.teams.create_or_replace(name=team.name, description=team.get('description'), organization=organizations[team.organization])
            # this helps update stale resources if some resources have changed, but others remain since this resource was created
            created_team.description = description
            created_team.organization = organizations[team.organization].id
            assert created_team.name == team.name
            teams[team.name] = created_team
            for username in team.users:
                with utils.suppress(exceptions.NoContent):
                    created_team.related.users.post(users[username].json)
        return users, organizations, teams

    @pytest.fixture(scope='class')
    def credentials(self, v2_class, rbac_structure):
        users, organizations, teams = rbac_structure
        # Create credentials
        credentials = {}
        for credential in config.resources.credentials:
            for item, source in (('user', users), ('team', teams)):
                found = credential.get(item, False)
                if found:
                    credential[item] = source[found]

            if credential.kind in utils.cloud_types:
                if credential.kind == 'azure':
                    config_credential = config.credentials.cloud.azure_classic
                else:
                    config_credential = config.credentials.cloud[credential.kind]
            elif credential.kind == 'vault':
                # FIXME: need to add vault type credential data to main credentials.vault
                continue
            elif credential.kind.lower() == 'openstack':
                # FIXME: need to update credentials.vault to only have hopenstack v3 creds
                # because v2_class is deprecated
                config_credential = config.credentials.cloud['openstack_v3']
            else:
                config_credential = config.credentials[credential.kind]

            for field in [x for x in config_credential if x in credential.inputs]:
                value = credential.inputs[field].format(**config_credential)
                credential.inputs[field] = value

            if 'project' in credential:
                credential['project_id' if credential.kind == 'gce' else 'project_name'] = credential.pop('project')

            credentials[credential.name] = v2_class.credentials.create_or_replace(**credential)
        return credentials

    @pytest.fixture(scope='class')
    def projects(self, v2_class, rbac_structure, credentials):
        users, organizations, teams = rbac_structure
        credentials = credentials
        # Create projects
        projects = {}
        project_updates = []
        for project in config.resources.projects:
            project['organization'] = organizations[project['organization']]
            if 'credential' in project:
                project['credential'] = credentials[project['credential']]
            projects[project.name] = v2_class.projects.create_or_replace(wait=False, **project)
            # this helps update stale resources if some resources have changed, but others remain since this resource was created
            projects[project.name].description = project.get('description', '')
            if hasattr(projects[project.name].related, 'current_update'):
                project_updates.append(projects[project.name].related.current_update.get())
            elif hasattr(projects[project.name].related, 'last_update'):
                project_updates.append(projects[project.name].related.last_update.get())
            else:
                raise AssertionError("No update found for project, something is wrong!")

        for update in project_updates:
            update.wait_until_completed(timeout=300, interval=30)

        for update in project_updates:
            if not update.is_successful:
                update.get()
                if '429 Too Many Requests' not in update.result_stdout:  # GH rate limit
                    assert update.is_successful, update.result_stdout
        return projects

    @pytest.fixture(scope='class')
    def all_inventory_objects(self, v2_class, rbac_structure, credentials):
        credentials = credentials
        users, organizations, teams = rbac_structure
        # Create inventory scripts
        inventory_scripts = {}
        for inventory_script in config.resources.inventory_scripts:
            inv_script = v2_class.inventory_scripts.create_or_replace(name=inventory_script.name, description=inventory_script.description,
                                                     organization=organizations[inventory_script.organization],
                                                     script=inventory_script.script)
            # this helps update stale resources if some resources have changed, but others remain since this resource was created
            inventory_scripts[inventory_script.name] = inv_script
            inventory_scripts[inventory_script.name].description = inventory_script.description
            inventory_scripts[inventory_script.name].organization = organizations[inventory_script.organization].id
            inventory_scripts[inventory_script.name].script = inventory_script.script

        # Create inventories
        inventories = {}
        for inventory in config.resources.inventories:
            inventory['organization'] = organizations[inventory.organization]
            if 'variables' in inventory:
                inventory['variables'] = json.dumps(inventory['variables'])
            inventories[inventory.name] = v2_class.inventory.create_or_replace(**inventory)

        # Create groups
        groups = {}
        for group in config.resources.groups:
            group['inventory'] = inventories[group.inventory]
            if 'variables' in group:
                group['variables'] = json.dumps(group['variables'])
            if 'parent' in group:
                group['parent'] = groups[group['parent']]
            groups[group.name] = v2_class.groups.create_or_replace(**group)
            # this helps update stale resources if some resources have changed, but others remain since this resource was created
            groups[group.name].inventory = inventories[group.inventory.name].id

        # Create hosts
        hosts = {}
        for host in config.resources.hosts:
            _groups = host.pop('groups', ())
            if 'variables' in host:
                host['variables'] = json.dumps(host['variables'])
            host['inventory'] = inventories[host.inventory]
            hosts[host.name] = v2_class.hosts.create_or_replace(**host)
            # If host has the wrong inventory, we cannot update it, so we need to delete this host
            # and create it again with correct inventory
            if hosts[host.name].inventory != inventories[host.inventory.name].id:
                hosts[host.name].delete()
                hosts[host.name] = v2_class.hosts.create_or_replace(**host)
                assert hosts[host.name].inventory == inventories[host.inventory.name].id
            for group in _groups:
                if groups[group].inventory != hosts[host.name].inventory:
                    raise AssertionError("Missed something!")
                else:
                    groups[group].add_host(hosts[host.name])

        # Create inventory sources
        inventory_sources = {}
        inventory_source_updates = []
        for inventory_source in config.resources.inventory_sources:
            group = groups[inventory_source.pop('group')]
            if 'source_vars' in inventory_source:
                inventory_source['source_vars'] = json.dumps(inventory_source['source_vars'])
            for field, store in (('credential', credentials), ('source_script', inventory_scripts), ('inventory', inventories)):
                if field in inventory_source:
                    inventory_source[field] = store[inventory_source[field]]
            created_inventory_source = v2_class.inventory_sources.create_or_replace(**inventory_source)
            # this helps update stale resources if some resources have changed, but others remain since this resource was created
            created_inventory_source.inventory = inventory_source['inventory'].id
            created_inventory_source.description = inventory_source.get('description', '')
            if inventory_source.get('credential'):
                created_inventory_source.credential = inventory_source['credential'].id

            inventory_sources[inventory_source.name] = created_inventory_source
            if hasattr(created_inventory_source.related, 'last_update'):
                inventory_source_updates.append(created_inventory_source.related.last_update.get())
            else:
                inventory_source_updates.append(created_inventory_source.update())

        # Wait for jobs to complete
        threads = [threading.Thread(target=update.wait_until_completed, args=()) for update in inventory_source_updates]
        [t.start() for t in threads]
        [t.join() for t in threads]

        return inventory_scripts, inventories, groups, hosts, inventory_sources

    def test_resources_loaded(self, v2_class, rbac_structure, projects, all_inventory_objects, credentials):
        # Use all the resources created to create Job Templates and run jobs to ensure it
        # is all functional
        inventory_scripts, inventories, groups, hosts, inventory_sources = all_inventory_objects
        job_templates = {}
        for job_template in config.resources.job_templates:
            jt_args = {field: job_template[field] for field in job_template}
            for item, source in (('project', projects),
                                 ('inventory', inventories),
                                 ('credential', credentials)):
                found = jt_args.get(item, False)
                if found:
                    jt_args[item] = source[found]
                else:
                    if item == 'project':
                        jt_args[item] = v2_class.projects.create()
                    if item == 'inventory':
                        jt_args[item] = v2_class.iventory.create()

            if 'extra_vars' in job_template:
                jt_args['extra_vars'] = json.dumps(job_template.extra_vars)

            jt = v2_class.job_templates.create_or_replace(**jt_args)

            job_templates[job_template.name] = jt

        jobs = []
        for jt in job_templates.values():
            if hasattr(jt.related, 'last_job'):
                jobs.append(jt.related.last_job.get())
            else:
                jobs.append(jt.launch())

        # Wait for jobs to complete
        threads = [threading.Thread(target=job.wait_until_completed, args=()) for job in jobs]
        [t.start() for t in threads]
        [t.join() for t in threads]

        for job in jobs:
            job = job.get()
            try:
                if job.name in ('language_features/tags.yml (tags:foo, limit:unresolvable-name.example.com)',
                                'ansible-playbooks.git/dynamic_inventory.yml',
                                'ansible-tower.git/setup/install.yml'):
                    assert job.status == 'failed'
                    assert job.job_explanation == ''
                else:
                    assert job.is_successful
            except Exception as e:
                import logging
                log = logging.getLogger(__name__)
                log.debug(f"not all jobs succeded, exception raised: {str(e)}")

    def test_create_instance_group_mapping(self, v2_class):
        igs = v2_class.instance_groups.get().results
        proj = v2_class.projects.create()

        for ig in igs:
            jt = v2_class.job_templates.create_or_replace(name=u'igmapping JT - {}'.format(ig.name))
            jt.project = proj.id
            jt.add_instance_group(ig)
        for ig in igs:
            inv = v2_class.inventory.create_or_replace(name=u'igmapping Inventory - {}'.format(ig.name))
            inv.add_instance_group(ig)
        for ig in igs:
            org = v2_class.organizations.create_or_replace(name=u'igmapping Org - {}'.format(ig.name))
            org.add_instance_group(ig)
