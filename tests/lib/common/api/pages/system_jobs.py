from common.api.pages import (Base_List, Job_Cancel_Page, Users_Page, Unified_Job_Page,
                              Unified_Job_Template_Page, System_Job_Template_Page, Notifications_Page,
                              json_setter, json_getter)


class System_Job_Page(Unified_Job_Page, System_Job_Template_Page):

    base_url = '/api/v1/system_jobs/{id}/'

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr == 'created_by':
            cls = Users_Page
        elif attr == 'unified_job_template':
            cls = Unified_Job_Template_Page
        elif attr == 'system_job_template':
            cls = System_Job_Template_Page
        elif attr == 'notifications':
            cls = Notifications_Page
        elif attr == 'cancel':
            cls = Job_Cancel_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)


class System_Jobs_Page(System_Job_Page, Base_List):

    base_url = '/api/v1/system_jobs/'


class System_Job_Cancel_Page(Unified_Job_Page, System_Job_Template_Page):

    base_url = '/api/v1/system_jobs/{id}/cancel'
    can_cancel = property(json_getter('can_cancel'), json_setter('can_cancel'))
