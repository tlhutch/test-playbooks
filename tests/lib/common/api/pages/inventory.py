from common.api import resources
import json

from common.api.pages import Unified_Job_Page, Unified_Job_Template_Page
import base


class Inventory_Page(base.Base):

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

base.register_page(resources.v1_inventory, Inventory_Page)


class Inventories_Page(Inventory_Page, base.Base_List):

    pass

base.register_page([resources.v1_inventories,
                    resources.v1_related_inventories], Inventories_Page)


class Group_Page(base.Base):

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

base.register_page(resources.v1_group, Group_Page)


class Groups_Page(Group_Page, base.Base_List):

    pass

base.register_page([resources.v1_groups,
                    resources.v1_host_groups,
                    resources.v1_inventory_related_groups,
                    resources.v1_group_children], Groups_Page)


class Host_Page(base.Base):

    pass

base.register_page(resources.v1_host, Host_Page)


class Hosts_Page(Host_Page, base.Base_List):

    pass

base.register_page([resources.v1_hosts,
                    resources.v1_group_related_hosts,
                    resources.v1_inventory_related_hosts], Hosts_Page)


class Fact_Version_Page(base.Base):

    pass

base.register_page(resources.v1_host_related_fact_version, Fact_Version_Page)


class Fact_Versions_Page(Fact_Version_Page, base.Base_List):

    @property
    def count(self):
        return len(self.results)

base.register_page(resources.v1_host_related_fact_versions, Fact_Versions_Page)


class Fact_View_Page(base.Base):

    pass

base.register_page(resources.v1_fact_view, Fact_View_Page)


class Inventory_Source_Page(Unified_Job_Template_Page):

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
        return self.source != "" and super(Inventory_Source_Page, self).is_successful

base.register_page(resources.v1_inventory_source, Inventory_Source_Page)


class Inventory_Sources_Page(Inventory_Source_Page, base.Base_List):

    pass

base.register_page([resources.v1_inventory_sources,
                    resources.v1_related_inventory_sources], Inventory_Sources_Page)


class Inventory_Source_Groups_Page(Group_Page, base.Base_List):

    pass

base.register_page(resources.v1_inventory_sources_related_groups, Inventory_Source_Groups_Page)


class Inventory_Source_Update_Page(base.Base):

    pass

base.register_page(resources.v1_inventory_sources_related_update, Inventory_Source_Update_Page)


class Inventory_Update_Page(Unified_Job_Page):

    pass

base.register_page(resources.v1_inventory_source_update, Inventory_Update_Page)


class Inventory_Updates_Page(Inventory_Update_Page, base.Base_List):

    pass

base.register_page(resources.v1_inventory_source_updates, Inventory_Updates_Page)


class Inventory_Update_Cancel_Page(base.Base):

    pass

base.register_page(resources.v1_inventory_source_update_cancel, Inventory_Update_Cancel_Page)


class Inventory_Script_Page(base.Base):

    pass

base.register_page(resources.v1_inventory_script, Inventory_Script_Page)


class Inventory_Scripts_Page(Inventory_Script_Page, base.Base_List):

    pass

base.register_page(resources.v1_inventory_scripts, Inventory_Scripts_Page)
