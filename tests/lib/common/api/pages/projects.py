import common.utils
from common.api.pages import json_getter, json_setter
from common.api.pages import Base, Base_List, Unified_Job_Page, Unified_Job_Template_Page


class Project_Page(Unified_Job_Template_Page):
    base_url = '/api/v1/projects/{id}/'
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

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name in ('last_update', 'last_job', 'current_update'):
            related = Project_Update_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'project_updates':
            related = Project_Updates_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'update':
            related = Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'playbooks':
            related = Playbooks_Page(self.testsetup, base_url=self.json['related'][name], objectify=False)
        elif name == 'organizations':
            from organizations import Organizations_Page
            related = Organizations_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'teams':
            from teams import Teams_Page
            related = Teams_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'schedules':
            from schedules import Schedules_Page
            related = Schedules_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'next_schedule':
            from schedules import Schedule_Page
            related = Schedule_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'activity_stream':
            from activity_stream import Activity_Stream_Page
            related = Activity_Stream_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

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


class Project_Update_Page(Unified_Job_Page):
    base_url = '/api/v1/project/{id}/update/'

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
