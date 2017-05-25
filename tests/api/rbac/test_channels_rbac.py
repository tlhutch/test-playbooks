from towerkit import utils, WSClient
import pytest

from tests.lib.helpers.workflow_utils import WorkflowTree, WorkflowTreeMapper
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class TestChannelsRBAC(Base_Api_Test):

        pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

        @pytest.mark.parametrize('role', ['ad hoc', 'admin', 'read', 'update', 'use'])
        def test_ad_hoc_command_events(self, request, factories, v2, role):
            """Confirm that a user is only alerted of ad hoc events when provided an allowed role"""
            inventory = factories.v2_host().ds.inventory
            user = factories.v2_user()
            ws = WSClient(v2.get_authtoken(user.username, user.password)).connect()
            request.addfinalizer(ws.close)

            ws.pending_ad_hoc_stdout()
            utils.logged_sleep(3)
            for m in ws:
                pass  # clear user identity

            ahc = factories.v2_ad_hoc_command(module_name='shell', module_args='true', inventory=inventory)
            ahc.wait_until_completed()
            received = [m for m in ws]
            denied_error = dict(error='access denied to channel ad_hoc_command_events for resource id {0.id}'
                                .format(ahc))
            assert denied_error in received

            assert inventory.set_object_roles(user, role)

            # subscribe to ahc as user
            ws.pending_ad_hoc_stdout()
            utils.logged_sleep(3)  # give Tower some time to process subscription
            ahc = ahc.relaunch().wait_until_completed()

            # keys where ws event doesn't match retrieved event for subtle reasons
            not_of_interest = set(('created', 'event_name', 'modified'))
            received = [m for m in ws]
            filtered_received = [{k: message[k] for k in set(message) - not_of_interest} for message in received]
            statuses = ('pending', 'waiting', 'running', 'successful')
            expected_status_changes = [dict(status=status,
                                            **dict(group_name='jobs', unified_job_id=ahc.id)) for status in statuses]
            for expected in expected_status_changes:
                assert expected in filtered_received
                filtered_received.remove(expected)

            with self.current_user(user.username, user.password):
                ahc_events = [result for result in ahc.related.events.get().results]
            assert ahc_events
            filtered_ahc_events = [{k: event[k] for k in set(event) - not_of_interest} for event in ahc_events]

            base_ahc_event = dict(ad_hoc_command=ahc.id, group_name='ad_hoc_command_events',
                                  type='ad_hoc_command_event')
            expected_ahc_events = [{k: v for d in [event, base_ahc_event] for k, v in d.items()}
                                   for event in filtered_ahc_events]
            for expected in expected_ahc_events:
                assert expected in filtered_received
                filtered_received.remove(expected)
            assert not filtered_received  # confirm no other messages received

        @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/5158')
        @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
        def test_inventory_update_status_changes(self, request, factories, v2, role):
            """Confirm that a user is only alerted of inventory source updates statuses when provided an allowed role"""
            user = factories.v2_user()
            ws = WSClient(v2.get_authtoken(user.username, user.password)).connect()
            request.addfinalizer(ws.close)
            ws.status_changes()
            utils.logged_sleep(3)
            for m in ws:
                pass  # clear user identity

            group = factories.v2_group(source='custom', inventory_script=True)
            group.related.inventory_source.get().update().wait_until_completed()
            assert not [m for m in ws]  # no messages should be broadcasted to client

            assert group.ds.inventory.set_object_roles(user, role)

            update_id = group.related.inventory_source.get().update().wait_until_completed().id
            base_status_change = dict(group_name='jobs', group_id=group.id, unified_job_id=update_id)
            statuses = ('pending', 'waiting', 'running', 'successful')
            expected = [dict(status=status, **base_status_change) for status in statuses]

            received = [m for m in ws]
            for message in expected:
                assert message in received
                received.remove(message)
            assert not received  # confirm no other messages received

        @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
        def test_job_events(self, request, factories, v2, role):
            """Confirm that a user is only alerted of job events when provided an allowed role"""
            user = factories.v2_user()
            inventory = factories.v2_host().ds.inventory
            jt = factories.v2_job_template(inventory=inventory)

            ws = WSClient(v2.get_authtoken(user.username, user.password)).connect()
            request.addfinalizer(ws.close)
            ws.pending_job_stdout()
            utils.logged_sleep(3)
            for m in ws:
                pass  # clear user identity

            job = jt.launch().wait_until_completed()
            received = [m for m in ws]
            denied_error = dict(error='access denied to channel job_events for resource id {0.id}'
                                .format(job))
            assert denied_error in received

            assert jt.set_object_roles(user, role)

            ws.pending_job_stdout()
            utils.logged_sleep(3)
            job = jt.launch().wait_until_completed()

            # keys where ws event doesn't match retrieved event for subtle reasons
            not_of_interest = set(('created', 'event_name', 'modified', 'summary_fields', 'related'))
            received = [m for m in ws]
            filtered_received = [{k: message[k] for k in set(message) - not_of_interest} for message in received]

            base_status_change = dict(group_name='jobs', unified_job_id=job.id)
            statuses = ('pending', 'waiting', 'running', 'successful')
            expected_status_changes = [dict(status=status, **base_status_change) for status in statuses]
            for expected in expected_status_changes:
                assert expected in filtered_received
                filtered_received.remove(expected)

            with self.current_user(user.username, user.password):
                job_events = [result.json for result in job.related.job_events.get().results]
            assert job_events
            filtered_job_events = [{k: event[k] for k in set(event) - not_of_interest} for event in job_events]

            base_job_event = dict(job=job.id, group_name='job_events', type='job_event')
            expected_job_events = [{k: v for d in [event, base_job_event] for k, v in d.items()}
                                   for event in filtered_job_events]
            for expected in expected_job_events:
                assert expected in filtered_received
                filtered_received.remove(expected)

            ws.unsubscribe()
            utils.logged_sleep(3)
            job.relaunch().wait_until_completed()

        @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/5158')
        @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
        def test_project_update_status_changes(self, request, factories, v2, role):
            """Confirm that a user is only alerted of project updates statuses when provided an allowed role"""
            user = factories.v2_user()
            ws = WSClient(v2.get_authtoken(user.username, user.password)).connect()
            request.addfinalizer(ws.close)
            ws.status_changes()
            utils.logged_sleep(3)
            for m in ws:
                pass  # clear user identity

            project = factories.v2_project()
            assert not [m for m in ws]  # no messages should be broadcasted to client

            assert project.set_object_roles(user, role)

            update_id = project.update().wait_until_completed().id
            base_status_change = dict(group_name='jobs', project_id=project.id, unified_job_id=update_id)
            statuses = ('pending', 'waiting', 'running', 'successful')
            expected = [dict(status=status, **base_status_change) for status in statuses]

            received = [m for m in ws]
            for message in expected:
                assert message in received
                received.remove(message)
            assert not received  # confirm no other messages received

        @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
        def test_workflow_events(self, request, factories, v2, role):
            """Confirm that a user is only alerted of workflow events when provided an allowed role"""
            user = factories.v2_user()
            ws = WSClient(v2.get_authtoken(user.username, user.password)).connect()
            request.addfinalizer(ws.close)
            inventory = factories.v2_host().ds.inventory
            success_jt = factories.job_template(inventory=inventory, playbook='debug.yml')
            fail_jt = factories.job_template(inventory=inventory, playbook='fail_unless.yml')
            wfjt = factories.workflow_job_template()
            root = factories.workflow_job_template_node(workflow_job_template=wfjt,
                                                        unified_job_template=success_jt)
            failure = root.related.success_nodes.post(dict(unified_job_template=fail_jt.id))
            success = failure.related.failure_nodes.post(dict(unified_job_template=success_jt.id))
            ws.pending_workflow_events()
            utils.logged_sleep(3)
            for m in ws:
                pass  # empty user indentifier

            wfj = wfjt.launch().wait_until_completed()
            ignored_success_ids = set(result.id for result in success_jt.related.jobs.get().results)
            ignored_fail_id = fail_jt.related.jobs.get().results.pop().id

            received = [m for m in ws]
            denied_error = dict(error='access denied to channel workflow_events for resource id {0.id}'
                                .format(wfj))
            assert denied_error in received

            for resource in (fail_jt, success_jt, wfjt):
                assert resource.set_object_roles(user, role)

            ws.pending_workflow_events()
            utils.logged_sleep(3)
            wfj = wfjt.launch().wait_until_completed()

            with self.current_user(user.username, user.password):
                success_job_ids = set(r.id for r in success_jt.related.jobs.get().results) - ignored_success_ids
                failure_job_id = filter(lambda x: x.id is not ignored_fail_id,
                                        fail_jt.related.jobs.get().results).pop().id

            mapper = WorkflowTreeMapper(WorkflowTree(wfjt), WorkflowTree(wfj)).map()
            base_workflow_event = dict(group_name='workflow_events', workflow_job_id=wfj.id)
            expected = []
            for workflow_node_id, job_id in zip((mapper[root.id], mapper[success.id]), success_job_ids):
                for status in ('pending', 'waiting', 'running', 'successful'):
                    expected.append(dict(status=status, workflow_node_id=workflow_node_id,
                                         unified_job_id=job_id, **base_workflow_event))
            for status in ('pending', 'waiting', 'running', 'failed'):
                expected.append(dict(status=status, workflow_node_id=mapper[failure.id],
                                     unified_job_id=failure_job_id, **base_workflow_event))

            received = [m for m in ws if m.get('group_name') == 'workflow_events']
            for message in expected:
                assert message in received
                received.remove(message)
