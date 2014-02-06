import base
from common.exceptions import *

class Job_Page(base.Task_Page):
    base_url = '/api/v1/jobs/{id}/'

    def get_related(self, name, **params):
        assert name in self.json['related']
        if name == 'job_events':
            related = Job_Events_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'start':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**params)

class Jobs_Page(Job_Page, base.Base_List):
    base_url = '/api/v1/jobs/'

class Job_Event_Page(base.Base):
    base_url = '/api/v1/jobs/{id}/job_events/{id}/'

    created = property(base.json_getter('created'), base.json_setter('created'))
    modified = property(base.json_getter('modified'), base.json_setter('modified'))
    job = property(base.json_getter('job'), base.json_setter('job'))
    event = property(base.json_getter('event'), base.json_setter('event'))
    event_display = property(base.json_getter('event_display'), base.json_setter('event_display'))
    failed = property(base.json_getter('failed'), base.json_setter('failed'))
    changed = property(base.json_getter('changed'), base.json_setter('changed'))
    host = property(base.json_getter('host'), base.json_setter('host'))
    parent = property(base.json_getter('parent'), base.json_setter('parent'))
    play = property(base.json_getter('play'), base.json_setter('play'))
    task = property(base.json_getter('task'), base.json_setter('task'))

class Job_Events_Page(Job_Event_Page, base.Base_List):
    base_url = '/api/v1/jobs/{id}/job_events/'
