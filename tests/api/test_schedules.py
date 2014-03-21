import pytest
import json
import yaml
import common.tower.license
import common.utils
from tests.api import Base_Api_Test

@pytest.mark.skip_selenium
@pytest.mark.nondestructive
# @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_1000')
@pytest.mark.usefixtures('authtoken')
class Test_Schedules_Project(Base_Api_Test):
    '''
    Test basic schedule CRUD operations: [GET, POST, PUT, PATCH, DELETE]

    Test schedule rrule support ...
      1. valid should be accepted
      2. invalid should return BadRequest

    Test related->project is correct?

    Create single schedule (rrule), verify ...
      1. project.next_update is expected
      2. project is updated at desired time

    Create multiple schedules (rrules), verify ...
      1. project.next_update is expected
      2. project is updated at desired time

    RBAC
      - admin can view/create/update/delete schedules
      - org_admin can view/create/update/delete schedules
      - user can *only* view schedules
      - user w/ update perm can *only* view/create/update schedules
    '''

    def test_schedule_get_empty(self, random_project):
        schedules_pg = random_project.get_related('schedules')
        assert schedules_pg.count == 0

    def test_schedule_post(self, random_project):
        pass

    def test_schedule_put(self, random_project):
        pass

    def test_schedule_patch(self, random_project):
        pass

    def test_schedule_get_again(self, random_project):

        schedules_pg = random_project.get_related('schedules')
        assert schedules_pg.count == 1

    def test_schedule_delete(self, random_project):
        pass
