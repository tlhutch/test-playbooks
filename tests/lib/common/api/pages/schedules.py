from common.api.pages import json_setter, json_getter, Base_List, Unified_Job_Page, Project_Page, Inventory_Page, Job_Template_Page, Jobs_Page


class Schedule_Page(Unified_Job_Page):
    base_url = '/api/v1/schedules/{id}/'
    name = property(json_getter('name'), json_setter('name'))
    type = property(json_getter('type'), json_setter('type'))
    description = property(json_getter('description'), json_setter('description'))
    enabled = property(json_getter('enabled'), json_setter('enabled'))
    dtstart = property(json_getter('dtstart'), json_setter('dtstart'))
    dtend = property(json_getter('dtend'), json_setter('dtend'))
    rrule = property(json_getter('rrule'), json_setter('rrule'))
    next_run = property(json_getter('next_run'), json_setter('next_run'))

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


class Schedules_Page(Schedule_Page, Base_List):
    base_url = '/api/v1/schedules/'
