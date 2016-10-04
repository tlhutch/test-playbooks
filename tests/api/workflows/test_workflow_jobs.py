import pytest
import logging

from tests.api import Base_Api_Test

# Job results
# [ ] Single node success
# [ ] Single failing node
# [ ] Node fails, triggers successful node
# [ ] Two branches, one node succeeds, other fails
# [ ] Individual job encounters error
# [ ] Workflow job encounters error
# [ ] Workflow job interrupted (e.g. by restarting tower)

# Job runs
# [ ] Node triggers success/failure/always nodes when appropriate
# [ ] Workflow includes multiple nodes that point to same unified job template
# [ ] Running concurrent workflows
# [ ] Changing job node while workflow is running
# [ ] Changing job template while workflow is running (change playbook, add survey, delete extra var..)
# [ ] Kicking off workflow when a job included in workflow has already been kicked off (as single job)
# [ ] Confirm including job template in workflow doesn't impair to run job template outside workflows
# [ ] Two workflows contain same node. Run both workflows at same time. Any collisions? (e.g. w/ artifacts)
# [ ] Using any misc settings (e.g. forks)

# Cancel
# [ ] Cancelling individual job in workflow
# [ ] Cancelling workflow
# [ ] (HA) Cancelling invidiual job in workflow

# Notifications
# [ ] For workflow's various states

# Timeouts
# [ ] On node
# [ ] On workflow

# Schedules
# [ ]

# Negative testing
# [ ] (-) No nodes
# [ ] (-) Delete unified job template used by node, run job
# [ ] (-) Delete unified job template used by node, while workflow in progress
# [ ] (-) Should not be able to re-run a job that was a part of a larger workflow job
# [ ] Delete a job that was part of a larger workflow job?
# [ ] (-) Delete workflow job while in progress
# [ ] Add new nodes to workflow while workflow is in progress

# Extra vars / Surveys / Prompting
# [ ] Workflow survey with non-default variable
# [ ] Job template prompts for credential, inventory, project, ..
# [ ] Create workflow, update node job template to require additional variable (using prompting, surveys)
# [ ] Variable precedence testing

# Artifacts (break out into separate test module?)
# [ ] Artifacts cumulative?
# [ ] Sensitive artifacts not exposed

# Workflows and HA
# [ ] Project update during workflow job, does project get copied over to other nodes (race condition?).
# [ ] (Similiar to above) Inventory updates lead to race condition?
# [ ] (-) Workflow running, node brought down

# Workflow job nodes
#

# Activity Stream
#

# Deleting
# [ ] Deleting workflow job (possible?)
# [ ] Delete workflow job template, confirm workflow job (and regular jobs triggered as well) deleted
# [ ] Orphaned workflow jobs

log = logging.getLogger(__name__)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Workflow_Jobs(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_here(self, factories):
        pass
