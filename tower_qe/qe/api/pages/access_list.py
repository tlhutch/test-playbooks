from qe.api import resources
import base


class AccessList(base.Base):

    pass

base.register_page([resources.v1_organization_access_list,
                    resources.v1_user_access_list,
                    resources.v1_inventory_access_list,
                    resources.v1_group_access_list,
                    resources.v1_credential_access_list,
                    resources.v1_project_access_list,
                    resources.v1_job_template_access_list,
                    resources.v1_team_access_list], AccessList)

# backwards compatibility
Access_List_Page = AccessList
