from qe.api.pages import UnifiedJob, JobTemplate
from qe.api import resources
import base


class Job(UnifiedJob, JobTemplate):

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

base.register_page(resources.v1_job, Job)


class Jobs(Job, base.BaseList):

    pass

base.register_page([resources.v1_jobs,
                    resources.v1_job_template_jobs,
                    resources.v1_system_job_template_jobs,
                    resources.v1_schedules_jobs], Jobs)


class JobCancel(UnifiedJob, JobTemplate):

    pass

base.register_page(resources.v1_job_cancel, JobCancel)


class JobEvent(base.Base):

    pass

base.register_page([resources.v1_job_event,
                    '/api/v1/jobs/\d+/job_events/\d+/'], JobEvent)


class JobEvents(JobEvent, base.BaseList):

    pass

base.register_page([resources.v1_job_events,
                    resources.v1_job_job_events,
                    resources.v1_job_event_children], JobEvents)


class JobPlay(base.Base):

    pass

base.register_page(resources.v1_job_play, JobPlay)


class JobPlays(JobPlay, base.BaseList):

    pass

base.register_page(resources.v1_job_plays, JobPlays)


class JobTask(base.Base):

    pass

base.register_page(resources.v1_job_task, JobTask)


class JobTasks(JobTask, base.BaseList):

    pass

base.register_page(resources.v1_job_tasks, JobTasks)


class JobHostSummary(base.Base):

    pass

base.register_page(resources.v1_job_host_summary, JobHostSummary)


class JobHostSummaries(JobHostSummary, base.BaseList):

    pass

base.register_page(resources.v1_job_host_summaries, JobHostSummaries)


class JobRelaunch(base.Base):

    pass

base.register_page(resources.v1_job_relaunch, JobRelaunch)


class JobStdout(base.Base):

    pass

base.register_page(resources.v1_job_stdout, JobStdout)

# backwards compatibility
Job_Page = Job
Jobs_Page = Jobs
Job_Cancel_Page = JobCancel
Job_Event_Page = JobEvent
Job_Events_Page = JobEvents
Job_Play_Page = JobPlay
Job_Plays_Page = JobPlays
Job_Task_Page = JobTask
Job_Tasks_Page = JobTasks
Job_Host_Summary_Page = JobHostSummary
Job_Host_Summaries_Page = JobHostSummaries
Job_Relaunch_Page = JobRelaunch
Job_Stdout_Page = JobStdout
