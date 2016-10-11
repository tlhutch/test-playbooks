from qe.api import resources
from jobs import UnifiedJob
import base


class AdHocCommand(UnifiedJob):

    def relaunch(self, payload={}):
        '''
        Relaunch the command using the related->relaunch endpoint
        '''
        # navigate to relaunch_pg
        relaunch = self.related.relaunch.get()

        # relaunch the command
        result = relaunch.post(payload)

        # return the corresponding command_pg
        return self.walk(result.url)

base.register_page(resources.v1_ad_hoc_commmand, AdHocCommand)


class AdHocCommands(base.BaseList, AdHocCommand):

    pass

base.register_page([resources.v1_ad_hoc_commmands,
                    resources.v1_inventory_related_ad_hoc_commands,
                    resources.v1_group_related_ad_hoc_commands,
                    resources.v1_host_related_ad_hoc_commands], AdHocCommands)

# backwards compatibility
Ad_Hoc_Command_Page = AdHocCommand
Ad_Hoc_Commands_Page = AdHocCommands
