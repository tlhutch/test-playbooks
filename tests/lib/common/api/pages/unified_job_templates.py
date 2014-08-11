import base
from common.exceptions import *

class Unified_Job_Template_Page(base.Base):
    base_url = '/api/v1/unified_job_templates/{id}/'

    name = property(base.json_getter('name'), base.json_setter('name'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'start':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

class Unified_Job_Templates_Page(Unified_Job_Template_Page, base.Base_List):
    base_url = '/api/v1/unified_job_templates/'
