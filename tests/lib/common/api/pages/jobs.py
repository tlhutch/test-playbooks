import base
from job_templates import Job_Template_Page


class Job_Page(base.Task_Page, Job_Template_Page):
    base_url = '/api/v1/jobs/{id}/'

    def get_related(self, name, **kwargs):
        assert name in self.json['related']
        if name == 'job_events':
            related = Job_Events_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_plays':
            related = Job_Plays_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_tasks':
            related = Job_Tasks_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'job_host_summaries':
            related = Job_Host_Summaries_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'start':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'cancel':
            related = Job_Cancel_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'credential':
            from credentials import Credential_Page
            related = Credential_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'cloud_credential':
            from credentials import Credential_Page
            related = Credential_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get(**kwargs)


class Jobs_Page(Job_Page, base.Base_List):
    base_url = '/api/v1/jobs/'


class Job_Cancel_Page(base.Task_Page, Job_Template_Page):
    base_url = '/api/v1/jobs/{id}/cancel'
    can_cancel = property(base.json_getter('can_cancel'), base.json_setter('can_cancel'))


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


class Job_Play_Page(base.Base):
    base_url = '/api/v1/jobs/{id}/job_plays/{id}/'

    id = property(base.json_getter('id'), base.json_setter('id'))
    play = property(base.json_getter('play'), base.json_setter('play'))
    started = property(base.json_getter('started'), base.json_setter('started'))
    changed = property(base.json_getter('changed'), base.json_setter('changed'))
    failed = property(base.json_getter('failed'), base.json_setter('failed'))
    ok_count = property(base.json_getter('ok_count'), base.json_setter('ok_count'))
    failed_count = property(base.json_getter('failed_count'), base.json_setter('failed_count'))
    changed_count = property(base.json_getter('changed_count'), base.json_setter('changed_count'))
    skipped_count = property(base.json_getter('skipped_count'), base.json_setter('skipped_count'))
    unreachable_count = property(base.json_getter('unreachable_count'), base.json_setter('unreachable_count'))


class Job_Plays_Page(Job_Play_Page, base.Base_List):
    base_url = '/api/v1/jobs/{id}/job_plays/'


class Job_Task_Page(base.Base):
    base_url = '/api/v1/jobs/{id}/job_tasks/{id}/'

    id = property(base.json_getter('id'), base.json_setter('id'))
    name = property(base.json_getter('name'), base.json_setter('name'))
    failed = property(base.json_getter('failed'), base.json_setter('failed'))
    changed = property(base.json_getter('changed'), base.json_setter('changed'))
    created = property(base.json_getter('created'), base.json_setter('created'))
    modified = property(base.json_getter('modified'), base.json_setter('modified'))
    reported_hosts = property(base.json_getter('reported_hosts'), base.json_setter('reported_hosts'))
    host_count = property(base.json_getter('host_count'), base.json_setter('host_count'))
    failed_count = property(base.json_getter('failed_count'), base.json_setter('failed_count'))
    unreachable_count = property(base.json_getter('unreachable_count'), base.json_setter('unreachable_count'))
    successful_count = property(base.json_getter('successful_count'), base.json_setter('successful_count'))
    changed_count = property(base.json_getter('changed_count'), base.json_setter('changed_count'))
    skipped_count = property(base.json_getter('skipped_count'), base.json_setter('skipped_count'))


class Job_Tasks_Page(Job_Task_Page, base.Base_List):
    base_url = '/api/v1/jobs/{id}/job_tasks/'


class Job_Host_Summary_Page(base.Base):
    base_url = '/api/v1/jobs/{id}/job_host_summaries/{id}/'

    play = property(base.json_getter('play'), base.json_setter('play'))
    job = property(base.json_getter('job'), base.json_setter('job'))
    host = property(base.json_getter('host'), base.json_setter('host'))
    changed = property(base.json_getter('changed'), base.json_setter('changed'))
    dark = property(base.json_getter('dark'), base.json_setter('dark'))
    ok = property(base.json_getter('ok'), base.json_setter('ok'))
    failures = property(base.json_getter('failures'), base.json_setter('failures'))
    processed = property(base.json_getter('processed'), base.json_setter('processed'))
    skipped = property(base.json_getter('skipped'), base.json_setter('skipped'))


class Job_Host_Summaries_Page(Job_Host_Summary_Page, base.Base_List):
    base_url = '/api/v1/jobs/{id}/job_host_summaries/'
