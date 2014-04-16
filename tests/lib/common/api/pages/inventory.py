import base
from common.exceptions import *

class Inventory_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/inventory/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    variables = property(base.json_getter('variables'), base.json_setter('variables'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'hosts':
            related = Hosts_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Inventories_Page(Inventory_Page, base.Base_List):
    base_url = '/api/v1/inventory/'

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'variable_data':
            related = Base_Page(self.testsetup, base_url=self.json['related'][name])
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

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'hosts':
            related = Hosts_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'inventory_source':
            related = Inventory_Source_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'children':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'variable_data':
            related = Base_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Groups_Page(Group_Page, base.Base_List):
    base_url = '/api/v1/groups/'

class Host_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/hosts/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    variables = property(base.json_getter('variables'), base.json_setter('variables'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'variable_data':
            related = Base_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'inventory':
            related = Inventory_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'groups':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Hosts_Page(Host_Page, base.Base_List):
    base_url = '/api/v1/hosts/'

class Inventory_Source_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/inventory_sources/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'last_update':
            related = Inventory_Update_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'inventory_updates':
            related = Inventory_Updates_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'update':
            # FIXME - this should have it's own object
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Inventory_Sources_Page(Inventory_Source_Page, base.Base_List):
    base_url = '/api/v1/inventory_sources/'

class Inventory_Update_Page(base.Task_Page):
    base_url = '/api/v1/inventory_updates/{id}/'

class Inventory_Updates_Page(Inventory_Update_Page, base.Base_List):
    base_url = '/api/v1/inventory_sources/{inventory_source}/inventory_updates/'
