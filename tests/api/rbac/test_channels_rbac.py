from awxkit.config import config as qe_config
from awxkit import utils, WSClient
from awxkit.api import Api
import pytest

from tests.lib.helpers.workflow_utils import WorkflowTree, WorkflowTreeMapper
from tests.api import APITest


@pytest.fixture
def user_ws_client(request, v2):
    def _ws_client(user):
        if qe_config.use_sessions:
            user_api = Api().load_session(user.username, user.password)
            kwargs = dict(
                session_id=user_api.connection.session_id,
                csrftoken=user_api.connection.session.cookies.get('csrftoken')
            )
        else:
            kwargs = dict(token=v2.get_authtoken(user.username, user.password))
        ws = WSClient(**kwargs)
        request.addfinalizer(ws.close)
        return ws
    return _ws_client


@pytest.mark.usefixtures('authtoken')
class TestChannelsRBAC(APITest):

    def sleep_and_clear_messages(self, ws):
        utils.logged_sleep(3)
        for m in ws:
            pass

    def test_ad_hoc_command_events_unauthorized_subscription(self, factories, user_ws_client):
        inventory = factories.host().ds.inventory
        user = factories.user()
        ws = user_ws_client(user).connect()
        ws.status_changes()
        self.sleep_and_clear_messages(ws)

        ahc = factories.ad_hoc_command(module_name='shell', module_args='true', inventory=inventory)
        ws.ad_hoc_stdout(ahc.id)
        ahc.wait_until_completed()
        received = [m for m in ws]
        denied_error = dict(error='access denied to channel ad_hoc_command_events for resource id {0.id}'
                                  .format(ahc))
        assert denied_error in received
        for msg in received:
            if msg != denied_error:
                assert msg['group_name'] == 'jobs'

    @pytest.mark.parametrize('role', ['ad hoc', 'admin', 'read', 'update', 'use'])
    def test_ad_hoc_command_events_with_allowed_role(self, factories, user_ws_client, role):
        """Confirm that a user is only alerted of ad hoc events when provided an allowed role"""
        inventory = factories.host().ds.inventory
        user = factories.user()
        assert inventory.set_object_roles(user, role)

        ws = user_ws_client(user).connect()
        ws.status_changes()
        self.sleep_and_clear_messages(ws)

        ahc = factories.ad_hoc_command(module_name='shell', module_args='true', inventory=inventory)
        ws.ad_hoc_stdout(ahc.id)
        ahc.wait_until_completed()

        # keys where ws event doesn't match retrieved event for subtle reasons
        not_of_interest = {'created', 'event_name', 'modified'}
        received = [m for m in ws]
        filtered_received = [{k: message[k] for k in set(message) - not_of_interest} for message in received]
        expected_status_changes = []
        for status in ('waiting', 'running', 'successful'):
            expected_msg = dict(status=status, group_name='jobs', unified_job_id=ahc.id, type=ahc.type)
            if status == 'waiting':
                expected_msg['instance_group_name'] = 'tower'
            expected_status_changes.append(expected_msg)
        for expected in expected_status_changes:
            assert expected in filtered_received
        filtered_received = [{
            'id': f['id'],
            'uuid': f['uuid'],
            'event': f['event']
        } for f in filtered_received if 'uuid' in f]

        with self.current_user(user.username, user.password):
            ahc_events = [result for result in ahc.related.events.get().results]
        assert ahc_events
        filtered_ahc_events = [{k: event[k] for k in set(event) - not_of_interest} for event in ahc_events]
        filtered_ahc_events = [{
            'id': f['id'],
            'uuid': f['uuid'],
            'event': f['event']
        } for f in filtered_ahc_events if 'uuid' in f]

        base_ahc_event = dict(ad_hoc_command=ahc.id, group_name='ad_hoc_command_events',
                              type='ad_hoc_command_event')
        expected_ahc_events = [{k: v for d in [event, base_ahc_event] for k, v in d.items()}
                               for event in filtered_ahc_events]
        for expected in expected_ahc_events:
            assert {
                'id': expected['id'],
                'uuid': expected['uuid'],
                'event': expected['event'],
            } in filtered_received

    def test_job_events_unauthorized_subscription(self, factories, user_ws_client):
        user = factories.user()
        inventory = factories.host().ds.inventory
        jt = factories.job_template(inventory=inventory)

        ws = user_ws_client(user).connect()
        ws.status_changes()
        self.sleep_and_clear_messages(ws)

        job = jt.launch()
        ws.job_stdout(job.id)
        job.wait_until_completed()
        received = [m for m in ws]
        denied_error = dict(error='access denied to channel job_events for resource id {0.id}'
                            .format(job))
        assert denied_error in received
        for msg in received:
            if msg != denied_error:
                assert msg['group_name'] == 'jobs'

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_job_events_with_allowed_role(self, factories, user_ws_client, role):
        """Confirm that a user is only alerted of job events when provided an allowed role"""
        user = factories.user()
        inventory = factories.host().ds.inventory
        jt = factories.job_template(inventory=inventory)
        assert jt.set_object_roles(user, role)

        ws = user_ws_client(user).connect()
        ws.status_changes()
        self.sleep_and_clear_messages(ws)

        job = jt.launch()
        ws.job_stdout(job.id)
        job.wait_until_completed()

        # keys where ws event doesn't match retrieved event for subtle reasons
        not_of_interest = {'created', 'event_name', 'modified', 'summary_fields', 'related'}
        received = [m for m in ws]
        filtered_received = [{k: message[k] for k in set(message) - not_of_interest} for message in received]

        base_status_change = dict(group_name='jobs', unified_job_id=job.id, type='job')
        expected_status_changes = []
        for status in ('waiting', 'running', 'successful'):
            expected_msg = dict(status=status, **base_status_change)
            if status == 'waiting':
                expected_msg['instance_group_name'] = 'tower'
            expected_status_changes.append(expected_msg)
        for expected in expected_status_changes:
            assert expected in filtered_received

        filtered_received = [{
            'id': f['id'],
            'uuid': f['uuid'],
            'event': f['event']
        } for f in filtered_received if 'uuid' in f]

        with self.current_user(user.username, user.password):
            job_events = [result.json for result in job.related.job_events.get().results]
        assert job_events
        filtered_job_events = [{k: event[k] for k in set(event) - not_of_interest} for event in job_events]

        base_job_event = dict(job=job.id, group_name='job_events', type='job_event')
        expected_job_events = [{k: v for d in [event, base_job_event] for k, v in d.items()}
                               for event in filtered_job_events]
        for expected in expected_job_events:
            assert {
                'id': expected['id'],
                'uuid': expected['uuid'],
                'event': expected['event']
            } in filtered_received

    @pytest.mark.github('https://github.com/ansible/tower/issues/669', skip=True)
    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_project_update_status_changes_with_allowed_role(self, factories, user_ws_client, role):
        """Confirm that a user is only alerted of project updates statuses when provided an allowed role"""
        user = factories.user()
        ws = user_ws_client(user).connect()
        ws.status_changes()
        self.sleep_and_clear_messages(ws)

        project = factories.project()
        assert not [m for m in ws]  # no messages should be broadcasted to client

        assert project.set_object_roles(user, role)

        update_id = project.update().wait_until_completed().id
        base_status_change = dict(group_name='jobs', project_id=project.id, unified_job_id=update_id)
        expected_status_changes = []
        for status in ('waiting', 'running', 'successful'):
            expected_msg = dict(status=status, **base_status_change)
            if status == 'waiting':
                expected_msg['instance_group_name'] = 'tower'
            expected_status_changes.append(expected_msg)

        received = [m for m in ws]
        for message in expected_status_changes:
            assert message in received

    def test_workflow_events_unauthorized_subscription(self, factories, user_ws_client):
        user = factories.user()
        ws = user_ws_client(user).connect()
        ws.status_changes()
        self.sleep_and_clear_messages(ws)

        inventory = factories.host().ds.inventory
        success_jt = factories.job_template(inventory=inventory, playbook='debug.yml')
        fail_jt = factories.job_template(inventory=inventory, playbook='fail_unless.yml')
        wfjt = factories.workflow_job_template()
        root = factories.workflow_job_template_node(workflow_job_template=wfjt,
                                                    unified_job_template=success_jt)
        failure = root.related.success_nodes.post(dict(unified_job_template=fail_jt.id))
        failure.related.failure_nodes.post(dict(unified_job_template=success_jt.id))

        wfj = wfjt.launch()
        ws.workflow_events(wfj.id)
        wfj.wait_until_completed()

        received = [m for m in ws]
        denied_error = dict(error='access denied to channel workflow_events for resource id {0.id}'
                            .format(wfj))
        assert denied_error in received
        for msg in received:
            if msg != denied_error:
                assert msg['group_name'] == 'jobs'

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_workflow_events_with_allowed_role(self, factories, user_ws_client, role):
        """Confirm that a user is only alerted of workflow events when provided an allowed role"""
        user = factories.user()
        inventory = factories.host().ds.inventory
        success_jt = factories.job_template(inventory=inventory, playbook='debug.yml')
        fail_jt = factories.job_template(inventory=inventory, playbook='fail_unless.yml')
        wfjt = factories.workflow_job_template()
        for resource in (fail_jt, success_jt, wfjt):
            assert resource.set_object_roles(user, role)

        root = factories.workflow_job_template_node(workflow_job_template=wfjt,
                                                    unified_job_template=success_jt)
        failure = root.related.success_nodes.post(dict(unified_job_template=fail_jt.id))
        success = failure.related.failure_nodes.post(dict(unified_job_template=success_jt.id))

        ws = user_ws_client(user).connect()
        ws.status_changes()
        self.sleep_and_clear_messages(ws)

        wfj = wfjt.launch()
        ws.workflow_events(wfj.id)
        wfj.wait_until_completed()

        with self.current_user(user.username, user.password):
            success_job_ids = [r.id for r in success_jt.related.jobs.get().results]
            failure_job_id = fail_jt.related.jobs.get().results.pop().id

        mapper = WorkflowTreeMapper(WorkflowTree(wfjt), WorkflowTree(wfj)).map()
        base_workflow_event = dict(group_name='workflow_events', workflow_job_id=wfj.id)

        expected = []
        for workflow_node_id, job_id in zip((mapper[root.id], mapper[success.id]), success_job_ids):
            for status in ('waiting', 'running', 'successful'):
                expected_msg = dict(status=status, workflow_node_id=workflow_node_id,
                                    unified_job_id=job_id, **base_workflow_event, type='job')
                if status == 'waiting':
                    expected_msg['instance_group_name'] = 'tower'
                expected.append(expected_msg)
        for status in ('waiting', 'running', 'failed'):
            expected_msg = dict(status=status, workflow_node_id=mapper[failure.id],
                                unified_job_id=failure_job_id, **base_workflow_event, type='job')
            if status == 'waiting':
                expected_msg['instance_group_name'] = 'tower'
            expected.append(expected_msg)

        received = [m for m in ws if m.get('group_name') == 'workflow_events']
        for message in expected:
            assert message in received
