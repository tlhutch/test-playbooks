from common.api import resources
import json

from common.api.pages import UnifiedJob, UnifiedJobTemplate
import base


class Inventory(base.Base):

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

base.register_page(resources.v1_inventory, Inventory)


class Inventories(Inventory, base.BaseList):

    pass

base.register_page([resources.v1_inventories,
                    resources.v1_related_inventories], Inventories)


class Group(base.Base):

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

base.register_page(resources.v1_group, Group)


class Groups(Group, base.BaseList):

    pass

base.register_page([resources.v1_groups,
                    resources.v1_host_groups,
                    resources.v1_inventory_related_groups,
                    resources.v1_group_children], Groups)


class Host(base.Base):

    pass

base.register_page(resources.v1_host, Host)


class Hosts(Host, base.BaseList):

    pass

base.register_page([resources.v1_hosts,
                    resources.v1_group_related_hosts,
                    resources.v1_inventory_related_hosts], Hosts)


class FactVersion(base.Base):

    pass

base.register_page(resources.v1_host_related_fact_version, FactVersion)


class FactVersions(FactVersion, base.BaseList):

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


class InventorySources(InventorySource, base.BaseList):

    pass

base.register_page([resources.v1_inventory_sources,
                    resources.v1_related_inventory_sources], InventorySources)


class InventorySourceGroups(Group, base.BaseList):

    pass

base.register_page(resources.v1_inventory_sources_related_groups, InventorySourceGroups)


class InventorySourceUpdate(base.Base):

    pass

base.register_page(resources.v1_inventory_sources_related_update, InventorySourceUpdate)


class InventoryUpdate(UnifiedJob):

    pass

base.register_page(resources.v1_inventory_source_update, InventoryUpdate)


class InventoryUpdates(InventoryUpdate, base.BaseList):

    pass

base.register_page(resources.v1_inventory_source_updates, InventoryUpdates)


class InventoryUpdateCancel(base.Base):

    pass

base.register_page(resources.v1_inventory_source_update_cancel, InventoryUpdateCancel)


class InventoryScript(base.Base):

    pass

base.register_page(resources.v1_inventory_script, InventoryScript)


class InventoryScripts(InventoryScript, base.BaseList):

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
