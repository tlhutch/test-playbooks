import json

from common.api.pages import Unified_Job_Page, Unified_Job_Template_Page
from common.api import resources
import base


class Project_Page(Unified_Job_Template_Page):

    def update(self):
        '''
        Update the project using related->update endpoint.
        '''
        # get related->launch
        update_pg = self.get_related('update')

        # assert can_update == True
        assert update_pg.can_update, \
            "The specified project (id:%s) is not able to update (can_update:%s)" % \
            (self.id, update_pg.can_update)

        # start the update
        result = update_pg.post()

        # assert JSON response
        assert 'project_update' in result.json, \
            "Unexpected JSON response when starting an project_update.\n%s" % \
            json.dumps(result.json, indent=2)

        # locate and return the specific update
        jobs_pg = self.get_related('project_updates', id=result.json['project_update'])
        assert jobs_pg.count == 1, \
            "An project_update started (id:%s) but job not found in response at %s/inventory_updates/" % \
            (result.json['project_update'], self.url)
        return jobs_pg.results[0]

    @property
    def is_successful(self):
        '''An project is considered successful when:
            0) scm_type != ""
            1) unified_job_template.is_successful
        '''
        return self.scm_type != "" and \
            super(Project_Page, self).is_successful

base.register_page(resources.v1_project, Project_Page)


class Projects_Page(Project_Page, base.Base_List):

    pass

base.register_page([resources.v1_projects,
                    resources.v1_related_project], Projects_Page)


class Project_Update_Page(Unified_Job_Page):

    pass

base.register_page(resources.v1_project_updates, Project_Update_Page)


class Project_Updates_Page(Project_Update_Page, base.Base_List):

    pass

base.register_page(resources.v1_projects_project_updates, Project_Updates_Page)


class Project_Update_Launch_Page(base.Base):

    pass

base.register_page(resources.v1_project_update, Project_Update_Launch_Page)


class Project_Update_Cancel_Page(base.Base):

    pass

base.register_page(resources.v1_project_update_cancel, Project_Update_Cancel_Page)


class Playbooks_Page(base.Base):

    pass

base.register_page(resources.v1_project_playbooks, Playbooks_Page)
