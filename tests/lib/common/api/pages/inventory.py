import time
import base
import common.utils
from common.exceptions import *

class Inventory_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/inventory/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

class Inventories_Page(Inventory_Page, base.Base_List):
    base_url = '/api/v1/inventory/'

class Group_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/groups/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, name):
        assert name in self.json['related']
        if name == 'hosts':
            related = Hosts_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'inventory_source':
            related = Inventory_Source_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'children':
            related = Groups_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Groups_Page(Group_Page, base.Base_List):
    base_url = '/api/v1/groups/'

class Host_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/hosts/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

class Hosts_Page(Host_Page, base.Base_List):
    base_url = '/api/v1/hosts/'

class Inventory_Source_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/inventory_sources/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, name):
        assert name in self.json['related']
        if name == 'last_update':
            related = Inventory_Update_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'inventory_updates':
            related = Inventory_Updates_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'update':
            # FIXME - this should have it's own object
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Inventory_Sources_Page(Inventory_Source_Page, base.Base_List):
    base_url = '/api/v1/inventory_sources/'

class Inventory_Update_Page(base.Base_List):
    base_url = '/api/v1/inventory_updates/{id}/'
    status = property(base.json_getter('status'), base.json_setter('status'))
    result_traceback = property(base.json_getter('result_traceback'), base.json_setter('result_traceback'))
    result_stdout = property(base.json_getter('result_stdout'), base.json_setter('result_stdout'))
    created = property(base.json_getter('created'), base.json_setter('created'))
    modified = property(base.json_getter('modified'), base.json_setter('failed'))

    @property
    def is_successful(self):
        return 'successful' == self.status.lower()

    def wait_until_completed(self, interval=5, verbose=0, timeout=60*8):
        return common.utils.wait_until(self, 'status', ('successful', 'failed', 'error', 'canceled',),
            interval=interval, verbose=verbose, timeout=timeout,
            start_time=time.strptime(self.created, '%Y-%m-%dT%H:%M:%S.%fZ'))

class Inventory_Updates_Page(Inventory_Update_Page, base.Base_List):
    base_url = '/api/v1/inventory_sources/{inventory_source}/inventory_updates/'
