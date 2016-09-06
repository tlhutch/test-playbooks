import fauxfactory

from qe.api.pages import Organization
from qe.api import resources
import base


class Team(base.Base):

    dependencies = [Organization]

    def add_permission(self, permission_type, project=None, inventory=None, run_ad_hoc_commands=None):
        perm_pg = self.get_related('permissions')
        payload = dict(name=fauxfactory.gen_utf8(),
                       description=fauxfactory.gen_utf8(),
                       user=self.id,
                       permission_type=permission_type,
                       project=project,
                       inventory=inventory,
                       run_ad_hoc_commands=run_ad_hoc_commands)
        result = perm_pg.post(payload)
        return result

    def create(self, name='', description='', organization=Organization, **kw):
        self.create_and_update_dependencies(organization)
        org_id = self.dependency_store[Organization].id
        payload = dict(name=name or 'Team - {}'.format(fauxfactory.gen_alphanumeric()),
                       description=description or fauxfactory.gen_alphanumeric(),
                       organization=org_id)
        return self.update_identity(Teams(self.testsetup).post(payload))

base.register_page(resources.v1_team, Team)


class Teams(base.BaseList, Team):

    pass

base.register_page([resources.v1_teams,
                    resources.v1_related_teams], Teams)

# backwards compatibility
Team_Page = Team
Teams_Page = Teams
