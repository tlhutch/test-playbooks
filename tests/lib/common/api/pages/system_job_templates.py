import base


class System_Job_Template_Page(base.Base):
    base_url = '/api/v1/system_job_templates/{id}/'

    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    status = property(base.json_getter('status'), base.json_setter('status'))
    type = property(base.json_getter('type'), base.json_setter('type'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'launch':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)


class System_Job_Templates_Page(System_Job_Template_Page, base.Base_List):
    base_url = '/api/v1/system_job_templates/'
