import pytest
import logging

from tests.api import Base_Api_Test

log = logging.getLogger(__name__)

# Creating
# [ ] Node using (a) job template (b) project update (c) inventory update
# [ ] API browser's json template for node includes {success,failure,always} nodes. Can you post values for these?
# [ ] Able to use same node in multiple workflows
# [ ] (-) Cannot use system job template
# [ ] (-) Cannot use workflow job template
# [ ] (-) Cannot create node without specifying unified_job_template
# [ ] (-) Cannot use bad id for unified job template / workflow template
# [ ] (-) Configure node to trigger itself (e.g. on success)

# Deleting
# [ ] Deleting unified job template used by node
# [ ] Deleting workflow job template used by node


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Workflow_Nodes(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_here(self, factories):
        pass
