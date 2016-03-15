from common.api.pages import json_setter, json_getter
from common.api.pages import Base, Base_List, Unified_Job_Template_Page


class System_Job_Template_Page(Unified_Job_Template_Page):
    base_url = '/api/v1/system_job_templates/{id}/'

    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    status = property(json_getter('status'), json_setter('status'))
    type = property(json_getter('type'), json_setter('type'))
    job_type = property(json_getter('job_type'), json_setter('job_type'))

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
        elif name == 'notification_templates_any':
            from notification_templates import Notification_Templates_Page
            related = Notification_Templates_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'notification_templates_error':
            from notification_templates import Notification_Templates_Page
            related = Notification_Templates_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'notification_templates_success':
            from notification_templates import Notification_Templates_Page
            related = Notification_Templates_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

    def launch(self, payload={}):
        '''
        Launch the system_job_template using related->launch endpoint.
        '''
        # get related->launch
        launch_pg = self.get_related('launch')

        # launch the job_template
        result = launch_pg.post(payload)

        # return job
        jobs_pg = self.get_related('jobs', id=result.json['system_job'])
        assert jobs_pg.count == 1, \
            "system_job_template launched (id:%s) but unable to find matching " \
            "job at %s/jobs/" % (result.json['job'], self.url)
        return jobs_pg.results[0]


class System_Job_Templates_Page(System_Job_Template_Page, Base_List):
    base_url = '/api/v1/system_job_templates/'
