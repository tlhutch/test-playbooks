from common.api.pages import Unified_Job_Page, System_Job_Template_Page
from common.api import resources
import base


class System_Job_Page(Unified_Job_Page, System_Job_Template_Page):

    pass

base.register_page(resources.v1_system_job, System_Job_Page)


class System_Jobs_Page(System_Job_Page, base.Base_List):

    pass

base.register_page(resources.v1_system_jobs, System_Jobs_Page)


class System_Job_Cancel_Page(Unified_Job_Page, System_Job_Template_Page):

    pass

base.register_page(resources.v1_system_job_cancel, System_Job_Cancel_Page)
