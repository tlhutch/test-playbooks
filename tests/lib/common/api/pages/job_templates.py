import base
from common.exceptions import *

class Job_Template_Page(base.Base):
    base_url = '/api/v1/job_templates/{id}/'

    name = property(base.json_getter('name'), base.json_setter('name'))
    inventory = property(base.json_getter('inventory'), base.json_setter('inventory'))
    project = property(base.json_getter('project'), base.json_setter('project'))
    playbook = property(base.json_getter('playbook'), base.json_setter('playbook'))
    forks = property(base.json_getter('forks'), base.json_setter('forks'))
    credential = property(base.json_getter('credential'), base.json_setter('credential'))
    extra_vars = property(base.json_getter('extra_vars'), base.json_setter('extra_vars'))

    def get_related(self, name):
        assert name in self.json['related']
        if name == 'start':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Job_Templates_Page(Job_Template_Page, base.Base_List):
    base_url = '/api/v1/job_templates/'
