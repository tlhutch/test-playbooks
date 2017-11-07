from towerkit import utils, WSClient
import pytest

from tests.lib.helpers.workflow_utils import WorkflowTree, WorkflowTreeMapper
from tests.api import Base_Api_Test


class ChannelsTest(object):

    def filtered_events(self, events, not_of_interest):
        filtered = []
        for event in events:
            filtered.append({k: event[k] for k in set(event) - set(not_of_interest)})
        return filtered

    def expected_events(self, events, base_event):
        return [{k: v for d in [event, base_event] for k, v in d.items()} for event in events]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestAdHocCommandChannels(ChannelsTest, Base_Api_Test):

        @pytest.fixture(scope='class')
        def ahc_and_ws_events(self, request, class_factories, v2_class):
            host = class_factories.v2_host()

            ws = WSClient(v2_class.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.pending_ad_hoc_stdout()
            utils.logged_sleep(3)
            for m in ws:
                pass

            ahc = class_factories.v2_ad_hoc_command(module_name='shell', module_args='true',
                                                    inventory=host.ds.inventory).wait_until_completed()
            assert ahc.is_successful
            messages = [m for m in ws]

            ws.unsubscribe()

            return ahc, messages

        @pytest.mark.ansible_integration
        @pytest.mark.mp_group('TestAdHocCommandChannelsSerialGroup', 'serial')
        @pytest.mark.parametrize('desired_status', ('pending', 'waiting', 'running', 'successful'))
        def test_ad_hoc_command_status_changes(self, ahc_and_ws_events, desired_status):
            ahc, events = ahc_and_ws_events
            desired_msg = dict(group_name='jobs', status=desired_status, unified_job_id=ahc.id)
            if desired_status == 'waiting':
                desired_msg['instance_group_name'] = 'tower'
            assert desired_msg in events

        @pytest.mark.ansible_integration
        @pytest.mark.mp_group('TestAdHocCommandChannelsSerialGroup', 'serial')
        def test_ad_hoc_command_events(self, ahc_and_ws_events):
            ahc, ws_events = ahc_and_ws_events

            # keys where ws event doesn't match retrieved event due to post-processing
            not_of_interest = ('created', 'event_name', 'modified')
            filtered_ws_events = self.filtered_events(ws_events, not_of_interest)

            ahc_events = [result for result in ahc.related.events.get().results]
            assert ahc_events

            filtered_ahc_events = self.filtered_events(ahc_events, not_of_interest)
            expected_ahc_events = self.expected_events(filtered_ahc_events, dict(ad_hoc_command=ahc.id,
                                                                                 group_name='ad_hoc_command_events',
                                                                                 type='ad_hoc_command_event'))
            for expected in expected_ahc_events:
                assert expected in filtered_ws_events

        def test_ad_hoc_command_events_unsubscribe(self, request, factories, v2):
            host = factories.v2_host()

            ws = WSClient(v2.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.pending_ad_hoc_stdout()
            utils.logged_sleep(3)
            for m in ws:
                pass

            ahc = factories.v2_ad_hoc_command(module_name='shell', module_args='true',
                                              inventory=host.ds.inventory).wait_until_completed()
            assert ahc.is_successful
            assert [m for m in ws]

            ws.unsubscribe()
            utils.logged_sleep(3)
            for m in ws:
                pass
            assert ahc.relaunch().wait_until_completed().is_successful
            assert not [m for m in ws]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobChannels(ChannelsTest, Base_Api_Test):

        @pytest.fixture(scope='class')
        def job_and_ws_events(self, request, class_factories, v2_class):
            host = class_factories.v2_host()

            ws = WSClient(v2_class.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.pending_job_stdout()
            utils.logged_sleep(3)
            for m in ws:
                pass

            job = class_factories.v2_job_template(playbook='debug.yml',
                                                  inventory=host.ds.inventory).launch().wait_until_completed()
            assert job.is_successful

            messages = [m for m in ws]

            ws.unsubscribe()

            return job, messages

        @pytest.mark.ansible_integration
        @pytest.mark.mp_group('TestJobChannelsSerialGroup', 'serial')
        @pytest.mark.parametrize('desired_status', ('pending', 'waiting', 'running', 'successful'))
        def test_job_command_status_changes(self, job_and_ws_events, desired_status):
            job, events = job_and_ws_events
            desired_msg = dict(group_name='jobs', status=desired_status, unified_job_id=job.id)
            if desired_status == 'waiting':
                desired_msg['instance_group_name'] = 'tower'
            assert desired_msg in events

        @pytest.mark.ansible_integration
        @pytest.mark.mp_group('TestJobChannelsSerialGroup', 'serial')
        def test_job_events(self, job_and_ws_events):
            job, ws_events = job_and_ws_events

            not_of_interest = ('created', 'event_name', 'modified', 'summary_fields', 'related')
            filtered_ws_events = self.filtered_events(ws_events, not_of_interest)

            job_events = [result for result in job.related.job_events.get().results]
            assert job_events

            filtered_ahc_events = self.filtered_events(job_events, not_of_interest)
            expected_ahc_events = self.expected_events(filtered_ahc_events, dict(job=job.id,
                                                                                 group_name='job_events',
                                                                                 type='job_event'))
            for expected in expected_ahc_events:
                assert expected in filtered_ws_events

        def test_job_events_unsubscribe(self, request, factories, v2):
            host = factories.v2_host()

            ws = WSClient(v2.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.pending_ad_hoc_stdout()
            utils.logged_sleep(3)
            for m in ws:
                pass

            job = factories.v2_job_template(playbook='debug.yml',
                                            inventory=host.ds.inventory).launch().wait_until_completed()
            assert job.is_successful
            assert [m for m in ws]

            ws.unsubscribe()
            utils.logged_sleep(3)
            for m in ws:
                pass
            assert job.relaunch().wait_until_completed().is_successful
            assert not [m for m in ws]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestWorkflowChannels(ChannelsTest, Base_Api_Test):

        @pytest.mark.ansible_integration
        def test_workflow_events(self, request, v1, factories):
            ws = WSClient(v1.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            inventory = factories.v2_host().ds.inventory
            success_jt = factories.v2_job_template(inventory=inventory, playbook='debug.yml')
            fail_jt = factories.v2_job_template(inventory=inventory, playbook='fail_unless.yml')
            wfjt = factories.v2_workflow_job_template()
            root = factories.v2_workflow_job_template_node(workflow_job_template=wfjt,
                                                           unified_job_template=success_jt)
            failure = root.related.success_nodes.post(dict(unified_job_template=fail_jt.id))
            success = failure.related.failure_nodes.post(dict(unified_job_template=success_jt.id))
            ws.pending_workflow_events()
            utils.logged_sleep(3)
            for m in ws:
                pass
            wfj = wfjt.launch().wait_until_completed()
            mapper = WorkflowTreeMapper(WorkflowTree(wfjt), WorkflowTree(wfj)).map()

            success_job_ids = [result.id for result in success_jt.related.jobs.get().results]
            failure_job_id = fail_jt.related.jobs.get().results.pop().id

            messages = [m for m in ws if m.get('group_name') == 'workflow_events']
            base_workflow_event = dict(group_name='workflow_events', workflow_job_id=wfj.id)
            expected = []
            for workflow_node_id, job_id in zip((mapper[root.id], mapper[success.id]), success_job_ids):
                for status in ('pending', 'waiting', 'running', 'successful'):
                    expected_msg = dict(status=status, workflow_node_id=workflow_node_id,
                                        unified_job_id=job_id, **base_workflow_event)
                    if status == 'waiting':
                        expected_msg['instance_group_name'] = 'tower'
                    expected.append(expected_msg)
            for status in ('pending', 'waiting', 'running', 'failed'):
                expected_msg = dict(status=status, workflow_node_id=mapper[failure.id],
                                    unified_job_id=failure_job_id, **base_workflow_event)
                if status == 'waiting':
                    expected_msg['instance_group_name'] = 'tower'
                expected.append(expected_msg)

            for message in expected:
                assert message in messages

            ws.unsubscribe()
            utils.logged_sleep(3)
            for m in ws:
                pass
            wfjt.launch().wait_until_completed()
            assert not [m for m in ws]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInventoryChannels(ChannelsTest, Base_Api_Test):

        @pytest.fixture(scope='class')
        def inv_update_and_ws_events(self, request, class_factories, v2_class):
            ws = WSClient(v2_class.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.status_changes()
            utils.logged_sleep(3)
            for m in ws:
                pass

            inv_update = class_factories.v2_inventory_source(source='custom').update().wait_until_completed()
            assert inv_update.is_successful
            messages = [m for m in ws]

            ws.unsubscribe()

            return inv_update, messages

        @pytest.mark.ansible_integration
        @pytest.mark.mp_group('TestInventoryChannelsSerialGroup', 'serial')
        @pytest.mark.parametrize('desired_status', ('pending', 'waiting', 'running', 'successful'))
        def test_inventory_update_status_changes(self, inv_update_and_ws_events, desired_status):
            inv_update, events = inv_update_and_ws_events
            desired_msg = dict(group_name='jobs',
                               status=desired_status,
                               unified_job_id=inv_update.id,
                               inventory_source_id=inv_update.inventory_source,
                               inventory_id=inv_update.related.inventory_source.get().inventory)
            if desired_status == 'waiting':
                desired_msg['instance_group_name'] = 'tower'
            assert desired_msg in events

        def test_inventory_update_events_unsubscribe(self, request, v2, factories):
            ws = WSClient(v2.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.status_changes()
            utils.logged_sleep(3)
            for m in ws:
                pass

            inv_source = factories.v2_inventory_source(source='custom')
            assert inv_source.update().wait_until_completed().is_successful
            assert [m for m in ws]

            ws.unsubscribe()
            utils.logged_sleep(3)
            for m in ws:
                pass
            assert inv_source.update().wait_until_completed().is_successful
            assert not [m for m in ws]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestProjectUpdateChannels(ChannelsTest, Base_Api_Test):

        @pytest.fixture(scope='class')
        def project_update_and_ws_events(self, request, class_factories, v2_class):
            ws = WSClient(v2_class.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.status_changes()
            utils.logged_sleep(3)
            for m in ws:
                pass

            project_update = class_factories.v2_project().update().wait_until_completed()
            assert project_update.is_successful
            messages = [m for m in ws]

            ws.unsubscribe()

            return project_update, messages

        @pytest.mark.ansible_integration
        @pytest.mark.mp_group('TestProjectUpdateChannelsSerialGroup', 'serial')
        @pytest.mark.parametrize('desired_status', ('pending', 'waiting', 'running', 'successful'))
        def test_project_update_status_changes(self, project_update_and_ws_events, desired_status):
            update, events = project_update_and_ws_events
            desired_msg = dict(group_name='jobs', project_id=update.project, unified_job_id=update.id,
                               status=desired_status)
            if desired_status == 'waiting':
                desired_msg['instance_group_name'] = 'tower'
            assert desired_msg in events

        @pytest.mark.ansible_integration
        def test_project_update_events_unsubscribe(self, request, v2, factories):
            ws = WSClient(v2.get_authtoken()).connect()
            request.addfinalizer(ws.close)
            ws.status_changes()
            utils.logged_sleep(3)
            for m in ws:
                pass

            project = factories.v2_project()
            assert project.update().wait_until_completed().is_successful
            assert [m for m in ws]

            ws.unsubscribe()
            utils.logged_sleep(3)
            for m in ws:
                pass
            assert project.update().wait_until_completed().is_successful
            assert not [m for m in ws]
