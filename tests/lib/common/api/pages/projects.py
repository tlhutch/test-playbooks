import json
from common.api.pages import json_getter, json_setter
from common.api.pages import Base, Base_List, Unified_Job_Page, Unified_Job_Template_Page


class Project_Page(Unified_Job_Template_Page):
    base_url = '/api/v1/projects/{id}/'
    type = property(json_getter('type'), json_setter('type'))
    local_path = property(json_getter('local_path'), json_setter('local_path'))
    scm_type = property(json_getter('scm_type'), json_setter('scm_type'))
    scm_url = property(json_getter('scm_url'), json_setter('scm_url'))
    scm_branch = property(json_getter('scm_branch'), json_setter('scm_branch'))
    scm_clean = property(json_getter('scm_clean'), json_setter('scm_clean'))
    scm_delete_on_update = property(json_getter('scm_delete_on_update'), json_setter('scm_delete_on_update'))
    scm_delete_on_next_update = property(json_getter('scm_delete_on_next_update'), json_setter('scm_delete_on_next_update'))
    scm_update_on_launch = property(json_getter('scm_update_on_launch'), json_setter('scm_update_on_launch'))
    scm_update_cache_timeout = property(json_getter('scm_update_cache_timeout'), json_setter('scm_update_cache_timeout'))
    has_schedules = property(json_getter('has_schedules'), json_setter('has_schedules'))
    summary_fields = property(json_getter('summary_fields'), json_setter('summary_fields'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr in ('last_update', 'last_job', 'current_update'):
            cls = Project_Update_Page
        elif attr == 'project_updates':
            cls = Project_Updates_Page
        elif attr == 'update':
            cls = Project_Update_Launch_Page
        elif attr == 'playbooks':
            cls = Playbooks_Page
        elif attr == 'organization':
            from organizations import Organization_Page
            cls = Organization_Page
        elif attr == 'teams':
            from teams import Teams_Page
            cls = Teams_Page
        elif attr == 'schedules':
            from schedules import Schedules_Page
            cls = Schedules_Page
        elif attr == 'next_schedule':
            from schedules import Schedule_Page
            cls = Schedule_Page
        elif attr == 'activity_stream':
            from activity_stream import Activity_Stream_Page
            cls = Activity_Stream_Page
        elif attr == 'notification_templates_any':
            from notification_templates import Notification_Templates_Page
            cls = Notification_Templates_Page
        elif attr == 'notification_templates_error':
            from notification_templates import Notification_Templates_Page
            cls = Notification_Templates_Page
        elif attr == 'notification_templates_success':
            from notification_templates import Notification_Templates_Page
            cls = Notification_Templates_Page
        elif attr == 'access_list':
            from access_list import Access_List_Page
            cls = Access_List_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)

    def update(self):
        '''
        Update the project using related->update endpoint.
        '''
        # get related->launch
        update_pg = self.get_related('update')

        # assert can_update == True
        assert update_pg.can_update, \
            "The specified project (id:%s) is not able to update (can_update:%s)" % \
            (self.id, update_pg.can_update)

        # start the update
        result = update_pg.post()

        # assert JSON response
        assert 'project_update' in result.json, \
            "Unexpected JSON response when starting an project_update.\n%s" % \
            json.dumps(result.json, indent=2)

        # locate and return the specific update
        jobs_pg = self.get_related('project_updates', id=result.json['project_update'])
        assert jobs_pg.count == 1, \
            "An project_update started (id:%s) but job not found in response at %s/inventory_updates/" % \
            (result.json['project_update'], self.url)
        return jobs_pg.results[0]

    @property
    def is_successful(self):
        '''An project is considered successful when:
            0) scm_type != ""
            1) unified_job_template.is_successful
        '''
        return self.scm_type != "" and \
            super(Project_Page, self).is_successful


class Projects_Page(Project_Page, Base_List):
    base_url = '/api/v1/projects/'


class Project_Update_Launch_Page(Base):
    base_url = '/api/v1/projects/{id}/update/'
    can_update = property(json_getter('can_update'), json_setter('can_update'))


class Project_Update_Page(Unified_Job_Page):
    base_url = '/api/v1/project_updates/{id}/'
    local_path = property(json_getter('local_path'), json_setter('local_path'))

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'cancel':
            related = Project_Update_Cancel_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)


class Project_Update_Cancel_Page(Base):
    base_url = '/api/v1/project_updates/{id}/cancel'
    can_cancel = property(json_getter('can_cancel'), json_setter('can_cancel'))


class Project_Updates_Page(Project_Update_Page, Base_List):
    base_url = '/api/v1/projects/{id}/project_updates/'


class Playbooks_Page(Base):
    base_url = '/api/v1/projects/{id}/playbooks/'
