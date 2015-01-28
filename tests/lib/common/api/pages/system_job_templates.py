from common.api.pages import json_setter, json_getter
from common.api.pages import Base, Base_List, Unified_Job_Template_Page


class System_Job_Template_Page(Unified_Job_Template_Page):
    base_url = '/api/v1/system_job_templates/{id}/'

    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    status = property(json_getter('status'), json_setter('status'))
    type = property(json_getter('type'), json_setter('type'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'launch':
            related = Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'jobs':
            from jobs import Jobs_Page
            related = Jobs_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)


class System_Job_Templates_Page(System_Job_Template_Page, Base_List):
    base_url = '/api/v1/system_job_templates/'
