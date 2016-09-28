import fauxfactory
import json

from qe.api.pages import Organization, UnifiedJob, UnifiedJobTemplate
from qe.config import config
from qe.api import resources
import base


class Project(UnifiedJobTemplate):

    dependencies = [Organization]

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

    def create(self, name='', scm_type='git', scm_url='', organization=Organization, **kw):
        name = name or 'Project - {}'.format(fauxfactory.gen_alphanumeric())
        scm_url = scm_url or config.project_urls[scm_type]
        self.create_and_update_dependencies(organization)
        org_id = self.dependency_store[Organization].id
        self.update_identity(Projects(self.testsetup).post(dict(name=name, scm_type=scm_type,
                                                                scm_url=scm_url, organization=org_id)))
        self.related.current_update.get().wait_until_completed()
        return self

base.register_page(resources.v1_project, Project)


class Projects(base.BaseList, Project):

    pass

base.register_page([resources.v1_projects,
                    resources.v1_related_project], Projects)


class ProjectUpdate(UnifiedJob):

    def cancel(self):
        # navigate to cancel_pg
        cancel_pg = self.get_related('cancel')

        # assert that project can get cancelled
        assert cancel_pg.can_cancel, \
            "cancel_pg 'can_cancel' is false - project update may have already completed."

        # cancel the project_update
        cancel_pg.post()

        # wait until project update is cancelled
        self.wait_until_status('running', timeout=30)

base.register_page(resources.v1_project_update, ProjectUpdate)


class ProjectUpdates(base.BaseList, ProjectUpdate):

    pass

base.register_page([resources.v1_project_updates,
                    resources.v1_project_project_updates], ProjectUpdates)


class ProjectUpdateLaunch(base.Base):

    pass

base.register_page(resources.v1_project_related_update, ProjectUpdateLaunch)


class ProjectUpdateCancel(base.Base):

    pass

base.register_page(resources.v1_project_update_cancel, ProjectUpdateCancel)


class Playbooks(base.Base):

    pass

base.register_page(resources.v1_project_playbooks, Playbooks)

# backwards compatibility
Project_Page = Project
Projects_Page = Projects
Project_Update_Page = ProjectUpdate
Project_Updates_Page = ProjectUpdates
Project_Update_Launch_Page = ProjectUpdateLaunch
Project_Update_Cancel_Page = ProjectUpdateCancel
Playbooks_Page = Playbooks
