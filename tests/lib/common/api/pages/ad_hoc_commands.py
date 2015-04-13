from common.api.pages import Base, Base_List, json_setter, json_getter
from jobs import Unified_Job_Page


class Ad_Hoc_Command_Page(Unified_Job_Page):
    '''
    Base class for ad hoc commands.
    '''
    base_url = '/api/v1/ad_hoc_commands/{id}/'
    '''
    name = property(json_getter('name'), json_setter('name'))
    launch_type = property(json_getter('launch_type'), json_setter('launch_type'))
    status = property(json_getter('status'), json_setter('status'))
    failed = property(json_getter('failed'), json_setter('failed'))
    result_stdout = property(json_getter('result_stdout'), json_setter('result_stdout'))
    job_type = property(json_getter('job_type'), json_setter('job_type'))
    inventory = property(json_getter('inventory'), json_setter('inventory'))
    credential = property(json_getter('credential'), json_setter('credential'))
    '''
    become_enabled = property(json_getter('become_enabled'), json_setter('become_enabled'))
    module_name = property(json_getter('module_name'), json_setter('module_name'))
    module_args = property(json_getter('module_args'), json_setter('module_args'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr == 'stdout':
            from jobs import Job_Stdout_Page
            cls = Job_Stdout_Page
        elif attr == 'inventory':
            from inventory import Inventory_Page
            cls = Inventory_Page
        elif attr == 'credential':
            from credentials import Credential_Page
            cls = Credential_Page
        elif attr == 'activity_stream':
            from activity_stream import Activity_Stream_Page
            cls = Activity_Stream_Page
        elif attr == 'events':
            from jobs import Job_Events_Page
            cls = Job_Events_Page
        elif attr == 'cancel':
            from jobs import Job_Cancel_Page
            cls = Job_Cancel_Page
        elif attr == 'relaunch':
            from jobs import Job_Relaunch_Page
            cls = Job_Relaunch_Page
        elif attr == 'created_by':
            from users import User_Page
            cls = User_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)


class Ad_Hoc_Commands_Page(Ad_Hoc_Command_Page, Base_List):
    base_url = '/api/v1/ad_hoc_commands/'
