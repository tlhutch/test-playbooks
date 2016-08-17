from common.api.pages import Unified_Job_Page
from common.api import resources
import base


class Schedule_Page(Unified_Job_Page):

    pass

base.register_page([resources.v1_schedule,
                    resources.v1_related_schedule], Schedule_Page)


class Schedules_Page(Schedule_Page, base.Base_List):

    pass

base.register_page([resources.v1_schedules,
                    resources.v1_related_schedules], Schedules_Page)
