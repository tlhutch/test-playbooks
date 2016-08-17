from common.api.pages import Unified_Job_Page, Job_Template_Page
from common.api import resources
import base


class Job_Page(Unified_Job_Page, Job_Template_Page):

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

base.register_page(resources.v1_job, Job_Page)


class Jobs_Page(Job_Page, base.Base_List):

    pass

base.register_page([resources.v1_jobs,
                    resources.v1_job_template_jobs,
                    resources.v1_system_job_template_jobs], Jobs_Page)


class Job_Cancel_Page(Unified_Job_Page, Job_Template_Page):

    pass

base.register_page(resources.v1_job_cancel, Job_Cancel_Page)


class Job_Event_Page(base.Base):

    pass

base.register_page([resources.v1_job_event,
                    '/api/v1/jobs/\d+/job_events/\d+/'], Job_Event_Page)


class Job_Events_Page(Job_Event_Page, base.Base_List):

    pass

base.register_page([resources.v1_job_events,
                    resources.v1_job_job_events,
                    resources.v1_job_event_children], Job_Events_Page)


class Job_Play_Page(base.Base):

    pass

base.register_page(resources.v1_job_play, Job_Play_Page)


class Job_Plays_Page(Job_Play_Page, base.Base_List):

    pass

base.register_page(resources.v1_job_plays, Job_Plays_Page)


class Job_Task_Page(base.Base):

    pass

base.register_page(resources.v1_job_task, Job_Task_Page)


class Job_Tasks_Page(Job_Task_Page, base.Base_List):

    pass

base.register_page(resources.v1_job_tasks, Job_Tasks_Page)


class Job_Host_Summary_Page(base.Base):

    pass

base.register_page(resources.v1_job_host_summary, Job_Host_Summary_Page)


class Job_Host_Summaries_Page(Job_Host_Summary_Page, base.Base_List):

    pass

base.register_page(resources.v1_job_host_summaries, Job_Host_Summaries_Page)


class Job_Relaunch_Page(base.Base):

    pass

base.register_page(resources.v1_job_relaunch, Job_Relaunch_Page)


class Job_Stdout_Page(base.Base):

    pass

base.register_page(resources.v1_job_stdout, Job_Stdout_Page)
