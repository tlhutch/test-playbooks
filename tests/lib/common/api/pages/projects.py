import time
import base
import common.utils
from common.exceptions import *

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
        elif name == 'organizations':
            from organizations import Organizations_Page
            related = Organizations_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'teams':
            from teams import Teams_Page
            related = Teams_Page(self.testsetup, base_url=self.json['related'][name])
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
    created = property(base.json_getter('created'), base.json_setter('created'))
    modified = property(base.json_getter('modified'), base.json_setter('failed'))

    @property
    def is_successful(self):
        return 'successful' == self.status.lower()

    def wait_until_completed(self, interval=5, verbose=0, timeout=60*8):
        return common.utils.wait_until(self, 'status', ('successful', 'failed', 'error', 'canceled',),
            interval=interval, verbose=verbose, timeout=timeout,
            start_time=time.strptime(self.created, '%Y-%m-%dT%H:%M:%S.%fZ'))

class Project_Updates_Page(Project_Update_Page, base.Base_List):
    base_url = '/api/v1/projects/{id}/project_updates/'
