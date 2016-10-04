import pytest
import logging

from tests.api import Base_Api_Test

log = logging.getLogger(__name__)

# Node RBAC
# [ ]

# Workflow RBAC
# [ ] Workflow nodes don't have organization field - how does tower let org admin view their workflows?
# [ ] Super user - has access to full CRUD
# [ ] Auditor - can view workflow/nodes (but not necessarily individual job templates / jobs)
# [ ]

# user capability fields
# [ ]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Workflow_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_here(self, factories):
        pass
