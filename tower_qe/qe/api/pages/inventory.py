import json
import re

import fauxfactory

from qe.api.pages import Organization, UnifiedJob, UnifiedJobTemplate
from qe.api import resources
import base


class Inventory(base.Base):

    dependencies = [Organization]

    def print_ini(self):
        '''Print an ini version of the inventory'''
        output = list()
        inv_dict = self.get_related('script', hostvars=1).json

        for group in inv_dict.keys():
            if group == '_meta':
                continue

            # output host groups
            output.append('[%s]' % group)
            for host in inv_dict[group].get('hosts', []):
                # FIXME ... include hostvars
                output.append(host)
            output.append('')  # newline

            # output child groups
            if inv_dict[group].get('children', []):
                output.append('[%s:children]' % group)
                for child in inv_dict[group].get('children', []):
                    output.append(child)
                output.append('')  # newline

            # output group vars
            if inv_dict[group].get('vars', {}).items():
                output.append('[%s:vars]' % group)
                for k, v in inv_dict[group].get('vars', {}).items():
                    output.append('%s=%s' % (k, v))
                output.append('')  # newline

        print '\n'.join(output)

    def create(self, name='', description='', organization=Organization, **kw):
        self.create_and_update_dependencies(organization)
        org_id = self.dependency_store[Organization].id
        payload = dict(name=name or 'Inventory - {}'.format(fauxfactory.gen_alphanumeric()),
                       description=description or fauxfactory.gen_alphanumeric(),
                       organization=org_id)
        return self.update_identity(Inventories(self.testsetup).post(payload))

base.register_page(resources.v1_inventory, Inventory)


class Inventories(base.BaseList, Inventory):

    pass

base.register_page([resources.v1_inventories,
                    resources.v1_related_inventories], Inventories)


class Group(base.Base):

    dependencies = [Inventory]

    @property
    def is_root_group(self):
        '''
        Returns whether the current group is a top-level root group in the inventory
        '''
        return self.get_related('inventory').get_related('root_groups', id=self.id).count == 1

    def get_parents(self):
        '''
        Inspects the API and returns all groups that include the current group
        as a child.
        '''
        parents = list()
        for candidate in self.get_related('inventory').get_related('groups').results:
            if candidate.get_related('children', id=self.id).count > 0:
                parents.append(candidate.id)
        return parents

    def create(self, name='', description='', inventory=Inventory, **kw):
        self.create_and_update_dependencies(inventory)
        inv_id = self.dependency_store[Inventory].id
        payload = dict(name=name if name else fauxfactory.gen_alphanumeric(),
                       description=description if description else fauxfactory.gen_alphanumeric(),
                       inventory=inv_id)
        return self.update_identity(Groups(self.testsetup).post(payload))

base.register_page(resources.v1_group, Group)


class Groups(base.BaseList, Group):

    pass

base.register_page([resources.v1_groups,
                    resources.v1_host_groups,
                    resources.v1_inventory_related_groups,
                    resources.v1_group_children], Groups)


class Host(base.Base):

    dependencies = [Inventory]

    def create(self, name='', description='', variables=None, inventory=Inventory, **kw):
        self.create_and_update_dependencies(inventory)
        inv_id = self.dependency_store[Inventory].id
        payload = dict(name=name or 'Host - {}'.format(fauxfactory.gen_alphanumeric()),
                       description=description or fauxfactory.gen_alphanumeric(),
                       variables=variables or json.dumps(dict(ansible_ssh_host='127.0.0.1',
                                                              ansible_connection='local')),
                       inventory=inv_id)
        return self.update_identity(Hosts(self.testsetup).post(payload))

base.register_page(resources.v1_host, Host)


class Hosts(base.BaseList, Host):

    pass

base.register_page([resources.v1_hosts,
                    resources.v1_group_related_hosts,
                    resources.v1_inventory_related_hosts], Hosts)


class FactVersion(base.Base):

    pass

base.register_page(resources.v1_host_related_fact_version, FactVersion)


class FactVersions(base.BaseList, FactVersion):

    @property
    def count(self):
        return len(self.results)

base.register_page(resources.v1_host_related_fact_versions, FactVersions)


class FactView(base.Base):

    pass

base.register_page(resources.v1_fact_view, FactView)


class InventorySource(UnifiedJobTemplate):

    def update(self):
        '''
        Update the inventory_source using related->update endpoint
        '''
        # get related->launch
        update_pg = self.get_related('update')

        # assert can_update == True
        assert update_pg.can_update, \
            "The specified inventory_source (id:%s) is not able to update (can_update:%s)" % \
            (self.id, update_pg.can_update)

        # start the inventory_update
        result = update_pg.post()

        # assert JSON response
        assert 'inventory_update' in result.json, \
            "Unexpected JSON response when starting an inventory_update.\n%s" % \
            json.dumps(result.json, indent=2)

        # locate and return the inventory_update
        jobs_pg = self.get_related('inventory_updates', id=result.json['inventory_update'])
        assert jobs_pg.count == 1, \
            "An inventory_update started (id:%s) but job not found in response at %s/inventory_updates/" % \
            (result.json['inventory_update'], self.url)
        return jobs_pg.results[0]

    @property
    def is_successful(self):
        '''An inventory_source is considered successful when:
            0) source != ""
            1) super().is_successful
        '''
        return self.source != "" and super(InventorySource, self).is_successful

base.register_page(resources.v1_inventory_source, InventorySource)


class InventorySources(base.BaseList, InventorySource):

    pass

base.register_page([resources.v1_inventory_sources,
                    resources.v1_related_inventory_sources], InventorySources)


class InventorySourceGroups(base.BaseList, Group):

    pass

base.register_page(resources.v1_inventory_sources_related_groups, InventorySourceGroups)


class InventorySourceUpdate(base.Base):

    pass

base.register_page(resources.v1_inventory_sources_related_update, InventorySourceUpdate)


class InventoryUpdate(UnifiedJob):

    pass

base.register_page(resources.v1_inventory_update, InventoryUpdate)


class InventoryUpdates(base.BaseList, InventoryUpdate):

    pass

base.register_page([resources.v1_inventory_updates,
                    resources.v1_inventory_source_updates], InventoryUpdates)


class InventoryUpdateCancel(base.Base):

    pass

base.register_page(resources.v1_inventory_update_cancel, InventoryUpdateCancel)


class InventoryScript(base.Base):

    dependencies = [Organization]

    def create(self, name='', description='', organization=Organization, script='', **kw):
        self.create_and_update_dependencies(organization)

        payload = dict()
        payload['organization'] = self.dependency_store[Organization].id
        payload['name'] = name or 'Inventory Script - {}'.format(fauxfactory.gen_alphanumeric())
        payload['description'] = description or 'Description - {}'.format(fauxfactory.gen_alphanumeric())
        payload['script'] = script or self._generate_script()

        return self.update_identity(InventoryScripts(self.testsetup).post(payload))

    def _generate_script(self):
            script = '\n'.join([
                u'#!/usr/bin/env python',
                u'# -*- coding: utf-8 -*-',
                u'import json',
                u'inventory = dict()',
                u'inventory["{0}"] = list()',
                u'inventory["{0}"].append("{1}")',
                u'inventory["{0}"].append("{2}")',
                u'inventory["{0}"].append("{3}")',
                u'inventory["{0}"].append("{4}")',
                u'inventory["{0}"].append("{5}")',
                u'print json.dumps(inventory)'
            ])
            group_name = re.sub(r"[\']", "", u"group-%s" % fauxfactory.gen_utf8())
            host_names = [re.sub(r"[\':]", "", u"host-%s" % fauxfactory.gen_utf8()) for _ in xrange(5)]

            return script.format(group_name, *host_names)


base.register_page(resources.v1_inventory_script, InventoryScript)


class InventoryScripts(base.BaseList, InventoryScript):

    pass

base.register_page(resources.v1_inventory_scripts, InventoryScripts)

# backwards compatibility
Inventory_Page = Inventory
Inventories_Page = Inventories
Group_Page = Group
Groups_Page = Groups
Host_Page = Host
Hosts_Page = Hosts
Fact_Version_Page = FactVersion
Fact_Versions_Page = FactVersions
Fact_View_Page = FactView
Inventory_Source_Page = InventorySource
Inventory_Sources_Page = InventorySources
Inventory_Source_Groups_Page = InventorySourceGroups
Inventory_Source_Update_Page = InventorySourceUpdate
Inventory_Update_Page = InventoryUpdate
Inventory_Updates_Page = InventoryUpdates
Inventory_Update_Cancel_Page = InventoryUpdateCancel
Inventory_Script_Page = InventoryScript
Inventory_Scripts_Page = InventoryScripts
