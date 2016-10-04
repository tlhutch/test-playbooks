import pytest
import logging

from tests.api import Base_Api_Test

log = logging.getLogger(__name__)

# Variations in structure
# [ ] Single node
# [ ] Multiple root nodes
# [ ] Node Depth > 1
# [ ] (-) Circular graph
# [ ] Can add node by (a) citing WFJT during node creation, (b) patching node w/ WFJT, (c) posting new node on /workflow_job_templates/\d+/workflow_nodes/

# Copy
# [ ]

# Labels
# [ ]

# Notifications
# [ ] On workflow job template
# [ ] On regular jobs

# Tags / Limits
# [ ]

# Extra vars
# [ ]

# Deleting
# [ ] Delete workflow with single node
# [ ] Delete intermediate node (with node(s) before/after)
# [ ] Delete leaf node
# [ ] Deleting root node when depth > 1
# [ ]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Workflow_Job_Templates(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_here(self, factories):
        pass
