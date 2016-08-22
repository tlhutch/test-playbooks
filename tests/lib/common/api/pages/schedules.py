from common.api.pages import UnifiedJob
from common.api import resources
import base


class Schedule(UnifiedJob):

    pass

base.register_page([resources.v1_schedule,
                    resources.v1_related_schedule], Schedule)


class Schedules(Schedule, base.BaseList):

    pass

base.register_page([resources.v1_schedules,
                    resources.v1_related_schedules], Schedules)

# backwards compatibility
Schedule_Page = Schedule
Schedules_Page = Schedules
