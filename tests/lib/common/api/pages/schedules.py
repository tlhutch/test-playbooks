import base
from projects import Project_Page
from inventory import Inventory_Page
from job_templates import Job_Template_Page
from common.exceptions import *

class Schedule_Page(base.Task_Page):
    base_url = '/api/v1/schedules/{id}/'

    def get_related(self, name, **params):
        assert name in self.json['related']
        if name == 'project':
            related = Project_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'inventory_update':
            related = Inventory_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_template':
            related = Job_Template_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**params)

class Schedules_Page(Schedule_Page, base.Base_List):
    base_url = '/api/v1/schedules/'
