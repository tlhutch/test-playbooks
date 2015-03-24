import json
from common.api.pages import Base, Base_List, Unified_Job_Page, Unified_Job_Template_Page, json_setter, json_getter


class Inventory_Page(Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/inventory/{id}/'
    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    variables = property(json_getter('variables'), json_setter('variables'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        if attr == 'hosts':
            related = Hosts_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'groups':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'inventory_source':
            related = Inventory_Source_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'root_groups':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'script':
            related = Base(self.testsetup, base_url=self.json['related'][attr])
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


class Inventories_Page(Inventory_Page, Base_List):
    base_url = '/api/v1/inventory/'

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        if attr == 'variable_data':
            related = Base(self.testsetup, base_url=self.json['related'][attr])
        else:
            raise NotImplementedError
        return related.get(**kwargs)


class Group_Page(Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/groups/{id}/'
    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    inventory = property(json_getter('inventory'), json_setter('inventory'))
    variables = property(json_getter('variables'), json_setter('variables'))

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
            related = Base(self.testsetup, base_url=self.json['related'][attr])
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


class Groups_Page(Group_Page, Base_List):
    base_url = '/api/v1/groups/'


class Host_Page(Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/hosts/{id}/'
    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    inventory = property(json_getter('inventory'), json_setter('inventory'))
    variables = property(json_getter('variables'), json_setter('variables'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        if attr == 'variable_data':
            related = Base(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'inventory':
            related = Inventory_Page(self.testsetup, base_url=self.json['related'][attr])
        elif attr == 'groups':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][attr])
        else:
            raise NotImplementedError
        return related.get(**kwargs)


class Hosts_Page(Host_Page, Base_List):
    base_url = '/api/v1/hosts/'


class Inventory_Source_Page(Unified_Job_Template_Page):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/inventory_sources/{id}/'

    source = property(json_getter('source'), json_setter('source'))
    source_vars = property(json_getter('source_vars'), json_setter('source_vars'))
    source_script = property(json_getter('source_script'), json_setter('source_script'))
    update_cache_timeout = property(json_getter('update_cache_timeout'), json_setter('update_cache_timeout'))
    update_on_launch = property(json_getter('update_on_launch'), json_setter('update_on_launch'))
    inventory = property(json_getter('inventory'), json_setter('inventory'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr
        cls = None
        if attr in ('last_update', 'current_update'):
            cls = Inventory_Update_Page
        elif attr == 'inventory_updates':
            cls = Inventory_Updates_Page
        elif attr == 'inventory':
            cls = Inventory_Page
        elif attr == 'update':
            cls = Inventory_Source_Update_Page
        elif attr == 'schedules':
            from schedules import Schedules_Page
            cls = Schedules_Page

        if cls is None:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)

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


class Inventory_Sources_Page(Inventory_Source_Page, Base_List):
    base_url = '/api/v1/inventory_sources/'


class Inventory_Source_Update_Page(Base):
    base_url = '/api/v1/inventory_sources/{id}/launch'
    can_update = property(json_getter('can_update'), json_setter('can_update'))


class Inventory_Update_Page(Unified_Job_Page):
    base_url = '/api/v1/inventory_updates/{id}/'


class Inventory_Updates_Page(Inventory_Update_Page, Base_List):
    base_url = '/api/v1/inventory_sources/{inventory_source}/inventory_updates/'


class Inventory_Script_Page(Base):
    base_url = '/api/v1/inventory_scripts/{id}/'
    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    script = property(json_getter('script'), json_setter('script'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related']
        raise NotImplementedError
        # return related.get(**kwargs)


class Inventory_Scripts_Page(Inventory_Script_Page, Base_List):
    base_url = '/api/v1/inventory_scripts/'
