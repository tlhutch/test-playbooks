import base
from projects import Project_Page
from inventory import Inventory_Page
from job_templates import Job_Template_Page
from jobs import Jobs_Page
from common.exceptions import *

class Schedule_Page(base.Task_Page):
    base_url = '/api/v1/schedules/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    enabled = property(base.json_getter('enabled'), base.json_setter('enabled'))
    dtstart = property(base.json_getter('dtstart'), base.json_setter('dtstart'))
    dtend = property(base.json_getter('dtend'), base.json_setter('dtend'))
    rrule = property(base.json_getter('rrule'), base.json_setter('rrule'))
    next_run = property(base.json_getter('next_run'), base.json_setter('next_run'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'project':
            related = Project_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'inventory_update':
            related = Inventory_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'unified_jobs':
            related = Jobs_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_template':
            related = Job_Template_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Schedules_Page(Schedule_Page, base.Base_List):
    base_url = '/api/v1/schedules/'
