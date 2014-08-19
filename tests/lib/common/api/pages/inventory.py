import base
from common.exceptions import *

class Inventory_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/inventory/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    variables = property(base.json_getter('variables'), base.json_setter('variables'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        if attr == 'hosts':
            related = Hosts_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'groups':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'root_groups':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'script':
            related = base.Base(self.testsetup, base_url=self.json['related'][attr])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

    def print_ini(self):
        '''
        Print an ini version of the inventory
        '''
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

class Inventories_Page(Inventory_Page, base.Base_List):
    base_url = '/api/v1/inventory/'

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        if attr == 'variable_data':
            related = base.Base(self.testsetup, base_url=self.json['related'][attr])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Group_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/groups/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    inventory = property(base.json_getter('inventory'), base.json_setter('inventory'))
    variables = property(base.json_getter('variables'), base.json_setter('variables'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        if attr == 'hosts':
            related = Hosts_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'all_hosts':
            related = Hosts_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'inventory':
            related = Inventory_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'inventory_source':
            related = Inventory_Source_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'children':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'variable_data':
            related = base.Base(self.testsetup, base_url=self.json['related'][attr])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

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

class Groups_Page(Group_Page, base.Base_List):
    base_url = '/api/v1/groups/'

class Host_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/hosts/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    inventory = property(base.json_getter('inventory'), base.json_setter('inventory'))
    variables = property(base.json_getter('variables'), base.json_setter('variables'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        if attr == 'variable_data':
            related = base.Base(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'inventory':
            related = Inventory_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'groups':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][attr])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Hosts_Page(Host_Page, base.Base_List):
    base_url = '/api/v1/hosts/'

class Inventory_Source_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/inventory_sources/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    source = property(base.json_getter('source'), base.json_setter('source'))
    status = property(base.json_getter('status'), base.json_setter('status'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    last_updated = property(base.json_getter('last_updated'), base.json_setter('last_updated'))
    last_update_failed = property(base.json_getter('last_update_failed'), base.json_setter('last_update_failed'))
    last_job_run = property(base.json_getter('last_job_run'), base.json_setter('last_job_run'))
    update_cache_timeout = property(base.json_getter('update_cache_timeout'), base.json_setter('update_cache_timeout'))
    update_on_launch = property(base.json_getter('update_on_launch'), base.json_setter('update_on_launch'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        if attr == 'last_update':
            related = Inventory_Update_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'current_update':
            related = Inventory_Update_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'inventory_updates':
            related = Inventory_Updates_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'update':
            # FIXME - this should have it's own object
            related = base.Base(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][attr])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

    @property
    def is_successful(self):
        '''An inventory_source is considered successful when:
            0) source != ""
            1) status == 'successful'
            2) not last_update_failed
            3) last_updated
        '''
        return self.source != "" and \
            self.status == 'successful' and \
            not self.last_update_failed and \
            self.last_updated is not None

class Inventory_Sources_Page(Inventory_Source_Page, base.Base_List):
    base_url = '/api/v1/inventory_sources/'

class Inventory_Update_Page(base.Task_Page):
    base_url = '/api/v1/inventory_updates/{id}/'

class Inventory_Updates_Page(Inventory_Update_Page, base.Base_List):
    base_url = '/api/v1/inventory_sources/{inventory_source}/inventory_updates/'
