from common.api.pages import UnifiedJob, SystemJobTemplate
from common.api import resources
import base


class SystemJob(UnifiedJob, SystemJobTemplate):

    pass

base.register_page(resources.v1_system_job, SystemJob)


class SystemJobs(SystemJob, base.BaseList):

    pass

base.register_page(resources.v1_system_jobs, SystemJobs)


class SystemJobCancel(UnifiedJob, SystemJobTemplate):

    pass

base.register_page(resources.v1_system_job_cancel, SystemJobCancel)

# backwards compatibility
System_Job_Page = SystemJob
System_Jobs_Page = SystemJobs
System_Job_Cancel_Page = SystemJobCancel
