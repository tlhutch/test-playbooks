import base
from common.exceptions import *

class Project_Page(base.Base):
    base_url = '/api/v1/projects/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    status = property(base.json_getter('status'), base.json_setter('status'))
    local_path = property(base.json_getter('local_path'), base.json_setter('local_path'))
    last_updated = property(base.json_getter('last_updated'), base.json_setter('last_updated'))
    last_update_failed = property(base.json_getter('last_update_failed'), base.json_setter('last_update_failed'))
    last_job_run = property(base.json_getter('last_job_run'), base.json_setter('last_job_run'))
    last_job_failed = property(base.json_getter('last_job_failed'), base.json_setter('last_job_failed'))
    scm_delete_on_next_update = property(base.json_getter('scm_delete_on_next_update'), base.json_setter('scm_delete_on_next_update'))
    scm_update_on_launch = property(base.json_getter('scm_update_on_launch'), base.json_setter('scm_update_on_launch'))
    scm_update_cache_timeout = property(base.json_getter('scm_update_cache_timeout'), base.json_setter('scm_update_cache_timeout'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'last_update':
            related = Project_Update_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'current_update':
            related = Project_Update_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'project_updates':
            related = Project_Updates_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'update':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'playbooks':
            related = Playbooks_Page(self.testsetup, base_url=self.json['related'][name], objectify=False)
        elif name == 'organizations':
            from organizations import Organizations_Page
            related = Organizations_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'teams':
            from teams import Teams_Page
            related = Teams_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Projects_Page(Project_Page, base.Base_List):
    base_url = '/api/v1/projects/'

class Project_Update_Page(base.Task_Page):
    base_url = '/api/v1/project/{id}/update/'

class Project_Updates_Page(Project_Update_Page, base.Base_List):
    base_url = '/api/v1/projects/{id}/project_updates/'

class Playbooks_Page(base.Base):
    base_url = '/api/v1/projects/{id}/playbooks/'
