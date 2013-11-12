import base
from common.exceptions import *

class Organization_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/organizations/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, name):
        assert name in self.json['related']
        if name == 'users':
            related = Users_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Organizations_Page(Organization_Page, base.Base_List):
    base_url = '/api/v1/organizations/'

class User_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/users/{id}/'
    username = property(base.json_getter('username'), base.json_setter('username'))
    first_name = property(base.json_getter('first_name'), base.json_setter('first_name'))
    last_name = property(base.json_getter('last_name'), base.json_setter('last_name'))

    def get_related(self, name):
        assert name in self.json['related']
        if name == 'credentials':
            related = Credentials_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Users_Page(User_Page, base.Base_List):
    base_url = '/api/v1/users/'

class Team_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/teams/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

class Teams_Page(Team_Page, base.Base_List):
    base_url = '/api/v1/teams/'

class Credential_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/credentials/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

class Credentials_Page(Credential_Page, base.Base_List):
    base_url = '/api/v1/credentials/'

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

class Inventory_Updates_Page(Inventory_Update_Page, base.Base_List):
    #base_url = '/api/v1/inventory_updates/'
    base_url = '/api/v1/inventory_sources/{inventory_source}/inventory_updates/'

class Project_Page(base.Base):
    base_url = '/api/v1/projects/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, name):
        assert name in self.json['related']
        if name == 'last_update':
            related = Project_Update_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'project_updates':
            related = Project_Updates_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'update':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Projects_Page(Project_Page, base.Base_List):
    base_url = '/api/v1/projects/'

class Project_Update_Page(base.Base_List):
    base_url = '/api/v1/project/{id}/update/'
    status = property(base.json_getter('status'), base.json_setter('status'))
    failed = property(base.json_getter('failed'), base.json_setter('failed'))
    result_traceback = property(base.json_getter('result_traceback'), base.json_setter('result_traceback'))
    result_stdout = property(base.json_getter('result_stdout'), base.json_setter('result_stdout'))

class Project_Updates_Page(Project_Update_Page, base.Base_List):
    base_url = '/api/v1/projects/{id}/project_updates/'

class Job_Template_Page(base.Base):
    base_url = '/api/v1/job_templates/{id}/'

    name = property(base.json_getter('name'), base.json_setter('name'))
    inventory = property(base.json_getter('inventory'), base.json_setter('inventory'))
    project = property(base.json_getter('project'), base.json_setter('project'))
    playbook = property(base.json_getter('playbook'), base.json_setter('playbook'))
    credential = property(base.json_getter('credential'), base.json_setter('credential'))

    def get_related(self, name):
        assert name in self.json['related']
        if name == 'start':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Job_Templates_Page(Job_Template_Page, base.Base_List):
    base_url = '/api/v1/job_templates/'

class Job_Page(base.Base):
    base_url = '/api/v1/jobs/{id}/'
    status = property(base.json_getter('status'), base.json_setter('status'))
    failed = property(base.json_getter('failed'), base.json_setter('failed'))
    result_traceback = property(base.json_getter('result_traceback'), base.json_setter('result_traceback'))
    result_stdout = property(base.json_getter('result_stdout'), base.json_setter('result_stdout'))

class Jobs_Page(Job_Page, base.Base_List):
    base_url = '/api/v1/jobs/'
