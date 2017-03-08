from towerkit import utils, WSClient
import pytest

from tests.lib.helpers.workflow_utils import WorkflowTree, WorkflowTreeMapper
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
class TestChannels(Base_Api_Test):

        pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

        def test_ad_hoc_command_events(self, request, v1):
            """Confirm that (un)subscriptions to status changed events and event emits are functional
            for ad hoc commands, and that ad_hoc_command_events match what's available at the command's
            relative events endpoint.
            """
            host = v1.hosts.create()
            request.addfinalizer(host.teardown)
            ws = WSClient(v1.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.pending_ad_hoc_stdout()
            utils.logged_sleep(3)  # give Tower some time to process subscription
            for m in ws:
                pass  # empty user indentifier
            ahc = v1.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=host.ds.inventory)
            request.addfinalizer(ahc.teardown)
            ahc.wait_until_completed()

            # keys where ws event doesn't match retrieved event for subtle reasons
            not_of_interest = set(('created', 'event_name', 'modified'))

            messages = [m for m in ws]
            filtered_messages = []
            for message in messages:
                filtered_messages.append({k: message[k] for k in set(message.keys()) - not_of_interest})

            base_status_change = dict(group_name='jobs', unified_job_id=ahc.id)
            statuses = ('pending', 'waiting', 'running', 'successful')
            expected_status_changes = [dict(status=status, **base_status_change) for status in statuses]
            for expected in expected_status_changes:
                assert(expected in filtered_messages)

            ahc_events = [result for result in ahc.related.events.get().results]
            assert(ahc_events)
            filtered_ahc_events = []
            for event in ahc_events:
                filtered_ahc_events.append({k: event[k] for k in set(event.keys()) - not_of_interest})

            base_ahc_event = dict(ad_hoc_command=ahc.id, group_name='ad_hoc_command_events',
                                  type='ad_hoc_command_event')
            expected_ahc_events = [{k: v for d in [event, base_ahc_event] for k, v in d.items()}
                                   for event in filtered_ahc_events]
            for expected in expected_ahc_events:
                assert(expected in filtered_messages)

            ws.unsubscribe()
            utils.logged_sleep(3)
            ahc.relaunch().wait_until_completed()
            assert(not [m for m in ws])  # no messages should be broadcasted to client

        def test_inventory_update_status_changes(self, request, v1):
            """Confirm that (un)subscriptions to status changed events and event emits are functional
            for inventory updates.
            """
            ws = WSClient(v1.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.status_changes()
            utils.logged_sleep(3)  # give Tower some time to process subscription
            for m in ws:
                pass  # empty user indentifier
            group = v1.groups.create(source='custom', inventory_script=True)
            request.addfinalizer(group.teardown)
            update_id = group.related.inventory_source.get().update().wait_until_completed().id
            messages = [m for m in ws]
            base_status_change = dict(group_name='jobs', group_id=group.id, unified_job_id=update_id)
            statuses = ('pending', 'waiting', 'running', 'successful')
            expected = [dict(status=status, **base_status_change) for status in statuses]
            for message in expected:
                assert(message in messages)

            ws.unsubscribe()
            utils.logged_sleep(3)
            group.related.inventory_source.get().update().wait_until_completed()
            assert(not [m for m in ws])  # no messages should be broadcasted to client

        def test_job_events(self, request, v1, factories):
            """Confirm that (un)subscriptions to status changed events and event emits are functional
            for launched jobs.
            """
            jt = factories.job_template(playbook='debug.yml')
            ws = WSClient(v1.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.pending_job_stdout()
            utils.logged_sleep(3)  # give Tower some time to process subscription
            for m in ws:
                pass  # empty user indentifier
            job = jt.launch().wait_until_completed()

            # keys where ws event doesn't match retrieved event for subtle reasons
            not_of_interest = set(('created', 'event_name', 'modified', 'summary_fields', 'related'))

            messages = [m for m in ws]
            filtered_messages = []
            for message in messages:
                filtered_messages.append({k: message[k] for k in set(message.keys()) - not_of_interest})

            base_status_change = dict(group_name='jobs', unified_job_id=job.id)
            statuses = ('pending', 'waiting', 'running', 'successful')
            expected_status_changes = [dict(status=status, **base_status_change) for status in statuses]
            for expected in expected_status_changes:
                assert(expected in filtered_messages)

            job_events = [result.json for result in job.related.job_events.get().results]
            assert(job_events)
            filtered_job_events = []
            for event in job_events:
                filtered_job_events.append({k: event[k] for k in set(event.keys()) - not_of_interest})

            base_job_event = dict(job=job.id, group_name='job_events', type='job_event')
            expected_job_events = [{k: v for d in [event, base_job_event] for k, v in d.items()}
                                   for event in filtered_job_events]
            for expected in expected_job_events:
                assert(expected in filtered_messages)

            ws.unsubscribe()
            utils.logged_sleep(3)
            job.relaunch().wait_until_completed()
            assert(not [m for m in ws])  # no messages should be broadcasted to client

        def test_project_update_status_changes(self, request, v1, factories):
            """Confirm that (un)subscriptions to status changed events and event emits are functional
            for project updates.
            """
            ws = WSClient(v1.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.status_changes()
            utils.logged_sleep(3)  # give Tower some time to process subscription
            for m in ws:
                pass  # empty user indentifier
            project = factories.project()
            update_id = project.related.project_updates.get().results.pop().id
            messages = [m for m in ws]
            base_status_change = dict(group_name='jobs', project_id=project.id, unified_job_id=update_id)
            statuses = ('pending', 'waiting', 'running', 'successful')
            expected = [dict(status=status, **base_status_change) for status in statuses]
            for message in expected:
                assert(message in messages)

            ws.unsubscribe()
            utils.logged_sleep(3)
            project.update().wait_until_completed()
            assert(not [m for m in ws])  # no messages should be broadcasted to client

        def test_workflow_events(self, request, v1, factories):
            """Confirm that (un)subscriptions to status changed events and event emits are functional
            for workflow jobs, and that workflow_events match what's available at the command's
            relative events endpoint.
            """
            ws = WSClient(v1.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            success_jt = factories.job_template(playbook='debug.yml')
            fail_jt = factories.job_template(playbook='fail_unless.yml')
            wfjt = factories.workflow_job_template()
            root = factories.workflow_job_template_node(workflow_job_template=wfjt,
                                                        unified_job_template=success_jt)
            failure = root.related.success_nodes.post(dict(unified_job_template=fail_jt.id))
            success = failure.related.failure_nodes.post(dict(unified_job_template=success_jt.id))
            ws.pending_workflow_events()
            utils.logged_sleep(3)  # give Tower some time to process subscription
            for m in ws:
                pass  # empty user indentifier
            wfj = wfjt.launch().wait_until_completed()
            mapper = WorkflowTreeMapper(WorkflowTree(wfjt), WorkflowTree(wfj)).map()

            success_job_ids = [result.id for result in success_jt.related.jobs.get().results]
            failure_job_id = fail_jt.related.jobs.get().results.pop().id

            messages = [m for m in ws if m.get('group_name') == 'workflow_events']
            base_workflow_event = dict(group_name='workflow_events', workflow_job_id=wfj.id)
            expected = []
            for workflow_node_id, job_id in zip((mapper[root.id], mapper[success.id]), success_job_ids):
                for status in ('pending', 'waiting', 'running', 'successful'):
                    expected.append(dict(status=status, workflow_node_id=workflow_node_id,
                                         unified_job_id=job_id, **base_workflow_event))
            for status in ('pending', 'waiting', 'running', 'failed'):
                expected.append(dict(status=status, workflow_node_id=mapper[failure.id],
                                     unified_job_id=failure_job_id, **base_workflow_event))

            for message in expected:
                assert(message in messages)

            ws.unsubscribe()
            utils.logged_sleep(3)
            wfjt.launch().wait_until_completed()
            assert(not [m for m in ws])  # no messages should be broadcasted to client
