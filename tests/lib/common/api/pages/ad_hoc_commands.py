from jobs import Unified_Job_Page
from common.api import resources
import base


class Ad_Hoc_Command_Page(Unified_Job_Page):

    pass

base.register_page(resources.v1_ad_hoc_commmand, Ad_Hoc_Command_Page)


class Ad_Hoc_Commands_Page(Ad_Hoc_Command_Page, base.Base_List):

    pass

base.register_page([resources.v1_ad_hoc_commmands,
                    resources.v1_inventory_related_ad_hoc_commands,
                    resources.v1_group_related_ad_hoc_commands,
                    resources.v1_host_related_ad_hoc_commands], Ad_Hoc_Commands_Page)
