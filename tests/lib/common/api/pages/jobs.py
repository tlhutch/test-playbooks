from common.api.pages import json_setter, json_getter, Base, Base_List, Unified_Job_Page, Job_Template_Page


class Job_Page(Unified_Job_Page, Job_Template_Page):
    base_url = '/api/v1/jobs/{id}/'

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'job_events':
            related = Job_Events_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_plays':
            related = Job_Plays_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_tasks':
            related = Job_Tasks_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_template':
            related = Job_Template_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_host_summaries':
            related = Job_Host_Summaries_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'start':
            related = Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'cancel':
            related = Job_Cancel_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'project':
            from projects import Project_Page
            related = Project_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'inventory':
            from inventory import Inventory_Page
            related = Inventory_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'credential':
            from credentials import Credential_Page
            related = Credential_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'cloud_credential':
            from credentials import Credential_Page
            related = Credential_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'relaunch':
            related = Job_Relaunch_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)

    # TODO: Other types of jobs support relaunch (system_job_templates), but
    # not all types (project_update, inventory_update).  As written, this
    # method only allows playbook_run relaunch.
    def relaunch(self, payload={}):
        '''
        Relaunch the job using related->relaunch endpoint
        '''
        # get related->launch
        relaunch_pg = self.get_related('relaunch')

        # relaunch the job using optionally provided payload
        result = relaunch_pg.post(payload)

        # locate corresponding job_pg
        jobs_pg = self.get_related('job_template').get_related('jobs', id=result.json['job'])
        assert jobs_pg.count == 1, \
            "unified_job id:%s was relaunched (id:%s) but no matching unified_job found" \
            (self.id, result.json['job'])

        # return job_pg
        return jobs_pg.results[0]


class Jobs_Page(Job_Page, Base_List):
    base_url = '/api/v1/jobs/'


class Job_Cancel_Page(Unified_Job_Page, Job_Template_Page):
    base_url = '/api/v1/jobs/{id}/cancel'
    can_cancel = property(json_getter('can_cancel'), json_setter('can_cancel'))


class Job_Event_Page(Base):
    base_url = '/api/v1/jobs/{id}/job_events/{id}/'

    created = property(json_getter('created'), json_setter('created'))
    modified = property(json_getter('modified'), json_setter('modified'))
    job = property(json_getter('job'), json_setter('job'))
    event = property(json_getter('event'), json_setter('event'))
    event_display = property(json_getter('event_display'), json_setter('event_display'))
    failed = property(json_getter('failed'), json_setter('failed'))
    changed = property(json_getter('changed'), json_setter('changed'))
    host = property(json_getter('host'), json_setter('host'))
    parent = property(json_getter('parent'), json_setter('parent'))
    play = property(json_getter('play'), json_setter('play'))
    task = property(json_getter('task'), json_setter('task'))


class Job_Events_Page(Job_Event_Page, Base_List):
    base_url = '/api/v1/jobs/{id}/job_events/'


class Job_Play_Page(Base):
    base_url = '/api/v1/jobs/{id}/job_plays/{id}/'

    id = property(json_getter('id'), json_setter('id'))
    play = property(json_getter('play'), json_setter('play'))
    started = property(json_getter('started'), json_setter('started'))
    changed = property(json_getter('changed'), json_setter('changed'))
    failed = property(json_getter('failed'), json_setter('failed'))
    ok_count = property(json_getter('ok_count'), json_setter('ok_count'))
    failed_count = property(json_getter('failed_count'), json_setter('failed_count'))
    changed_count = property(json_getter('changed_count'), json_setter('changed_count'))
    skipped_count = property(json_getter('skipped_count'), json_setter('skipped_count'))
    unreachable_count = property(json_getter('unreachable_count'), json_setter('unreachable_count'))


class Job_Plays_Page(Job_Play_Page, Base_List):
    base_url = '/api/v1/jobs/{id}/job_plays/'


class Job_Task_Page(Base):
    base_url = '/api/v1/jobs/{id}/job_tasks/{id}/'

    id = property(json_getter('id'), json_setter('id'))
    name = property(json_getter('name'), json_setter('name'))
    failed = property(json_getter('failed'), json_setter('failed'))
    changed = property(json_getter('changed'), json_setter('changed'))
    created = property(json_getter('created'), json_setter('created'))
    modified = property(json_getter('modified'), json_setter('modified'))
    reported_hosts = property(json_getter('reported_hosts'), json_setter('reported_hosts'))
    host_count = property(json_getter('host_count'), json_setter('host_count'))
    failed_count = property(json_getter('failed_count'), json_setter('failed_count'))
    unreachable_count = property(json_getter('unreachable_count'), json_setter('unreachable_count'))
    successful_count = property(json_getter('successful_count'), json_setter('successful_count'))
    changed_count = property(json_getter('changed_count'), json_setter('changed_count'))
    skipped_count = property(json_getter('skipped_count'), json_setter('skipped_count'))


class Job_Tasks_Page(Job_Task_Page, Base_List):
    base_url = '/api/v1/jobs/{id}/job_tasks/'


class Job_Host_Summary_Page(Base):
    base_url = '/api/v1/jobs/{id}/job_host_summaries/{id}/'

    play = property(json_getter('play'), json_setter('play'))
    job = property(json_getter('job'), json_setter('job'))
    host = property(json_getter('host'), json_setter('host'))
    changed = property(json_getter('changed'), json_setter('changed'))
    dark = property(json_getter('dark'), json_setter('dark'))
    ok = property(json_getter('ok'), json_setter('ok'))
    failures = property(json_getter('failures'), json_setter('failures'))
    processed = property(json_getter('processed'), json_setter('processed'))
    skipped = property(json_getter('skipped'), json_setter('skipped'))


class Job_Host_Summaries_Page(Job_Host_Summary_Page, Base_List):
    base_url = '/api/v1/jobs/{id}/job_host_summaries/'


class Job_Relaunch_Page(Base):
    base_url = '/api/v1/jobs/{id}/relaunch/'

    passwords_needed_to_start = property(json_getter('passwords_needed_to_start'), json_setter('passwords_needed_to_start'))
