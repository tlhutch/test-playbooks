import logging

import fauxfactory
from awxkit import utils
import awxkit.exceptions
import pytest
import six
import json
import yaml

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('authtoken')
class TestActivityStream(APITest):

    @pytest.mark.parametrize('resource', ['schedule', 'survey', 'job_template', 'workflow_job_template', 'credential',
                                          'credential_type', 'project', 'inventory', 'group', 'host', 'inventory_script',
                                          'organization', 'user', 'team', 'instance_group'])
    def test_deleted_resources_logged_as_deleted_user(self, v2, factories, resource):
        is_survey = False
        if resource == 'schedule':
            resource = factories.job_template().add_schedule()
        elif resource == 'survey':
            is_survey = True
            resource = factories.job_template().add_survey()
        elif resource in ('credential_type', 'instance_group'):
            resource = getattr(factories, resource)()
        else:
            resource = getattr(factories, resource)()
        superuser = factories.user(is_superuser=True)

        with self.current_user(superuser):
            resource.delete()
        superuser.delete()

        as_entries = v2.activity_stream.get(deleted_actor__contains=superuser.username).results
        assert len(as_entries) == 1
        as_entry = as_entries.pop()

        if is_survey:
            # The deletion of the survey is actually an update to the Job
            # Template
            assert as_entry.object1 == 'job_template'
            assert as_entry.operation == 'update'
        else:
            assert as_entry.object1 == resource.type
            assert as_entry.operation == 'delete'

        assert not as_entry.object2
        assert as_entry.summary_fields.actor.username == superuser.username
        assert as_entry.summary_fields.actor.first_name == superuser.first_name
        assert as_entry.summary_fields.actor.last_name == superuser.last_name

    @pytest.mark.yolo
    @pytest.mark.parametrize('fixture, method', [('job_template_plain', 'launch'),
                                                 ('workflow_job_template', 'launch'),
                                                 ('ad_hoc_command', None),
                                                 ('project', 'update'),
                                                 ('custom_inventory_source', 'update'),
                                                 ('cleanup_jobs_template', 'launch')],
                             ids=['job', 'workflow job', 'ad hoc command', 'project_update',
                                  'inventory_update', 'system job'])
    def test_deleted_uj_logged_as_deleted_user(self, request, v2, factories, fixture, method):
        superuser = factories.user(is_superuser=True)

        if method:
            resource = request.getfixturevalue(fixture)
            uj = getattr(resource, method)().wait_until_completed()
        else:
            uj = request.getfixturevalue(fixture).wait_until_completed()

        with self.current_user(superuser):
            uj.delete()
        superuser.delete()

        if uj.type in ('job', 'workflow_job', 'ad_hoc_command'):
            as_entry = v2.activity_stream.get(deleted_actor__contains=superuser.username).results.pop()
            assert as_entry.object1 == uj.type
            assert not as_entry.object2
            assert as_entry.operation == 'delete'
            assert as_entry.summary_fields.actor.username == superuser.username
            assert as_entry.summary_fields.actor.first_name == superuser.first_name
            assert as_entry.summary_fields.actor.last_name == superuser.last_name
        else:
            assert v2.activity_stream.get(deleted_actor__contains=superuser.username).count == 0

    def test_limited_view_of_unprivileged_user(self, factories, api_activity_stream_pg, user_password):
        """Confirms that unprivileged users only see their creation details in activity stream"""
        activity = api_activity_stream_pg
        user = factories.user(organization=factories.organization())

        # generate activity that user shouldn't have access to in activity stream
        for _ in range(3):
            org = factories.organization()
            for _ in range(5):
                factories.credential(user=factories.user(organization=org), organization=None)

        with self.current_user(user.username, user_password):
            activity.get()

        # confirm that only user creation events for user in question are shown
        for result in activity.results:
            try:
                assert result.summary_fields.user[0].username == user.username
            except AttributeError:
                # roll JSON_Wrapper Attribute errors in here too
                raise Exception("Unprivileged user has access to unexpected activity stream content.")

    def test_inventory_id_in_group_activity_stream(self, factories):
        """Confirms that inventory_id is included in the group summary_fields for all non-delete operations"""
        inventory = factories.inventory()
        group = factories.group(inventory=inventory)
        host = factories.host(inventory=inventory)

        group.name = "UpdatedGroupName"
        with pytest.raises(awxkit.exceptions.NoContent):
            group.get_related('hosts').post(dict(associate=True, id=host.id))
        with pytest.raises(awxkit.exceptions.NoContent):
            group.get_related('hosts').post(dict(disassociate=True, id=host.id))

        operations = ['create', 'update', 'associate', 'disassociate']

        activity = group.get_related('activity_stream')
        for result in activity.results:
            assert 'inventory_id' in result.summary_fields.group[0]
            operations.remove(result.operation)

        assert(not operations
               ), "Failed to find activity for all operations.  Missing: {}".format(operations)

    def test_verify_configure_tower_edit_entry(self, v2, superuser, update_setting_pg):
        jobs_settings = v2.settings.get().get_endpoint('jobs')
        payload = dict(SCHEDULE_MAX_JOBS=777)
        with self.current_user(superuser):
            update_setting_pg(jobs_settings, payload)

        activity = v2.activity_stream.get(actor=superuser.id).results.pop()
        summary_fields = activity.summary_fields

        assert summary_fields.setting == [dict(category='jobs', name='SCHEDULE_MAX_JOBS')]
        assert summary_fields.actor.username == superuser.username
        assert summary_fields.actor.first_name == superuser.first_name
        assert summary_fields.actor.last_name == superuser.last_name
        assert summary_fields.actor.id == superuser.id

        assert activity.object1 == "setting"
        assert activity.object2 == ""
        assert activity.type == "activity_stream"
        assert activity.operation == "create"
        assert activity.object_association == ""

    @pytest.mark.parametrize('template', ['job', 'workflow_job'])
    def test_survey_password_defaults_not_exposed_upon_template_deletion(self, v2, factories, superuser, template):
        resource = getattr(factories, template + '_template')()
        password = "don't expose me - {0}".format(utils.random_utf8().encode('utf8'))
        survey = [dict(required=False,
                       question_name='Test',
                       variable='var',
                       type='password',
                       default=password)]
        resource.add_survey(spec=survey)

        with self.current_user(superuser):
            resource.delete()
        activity = v2.activity_stream.get(actor=superuser.id).results.pop()
        spec = utils.load_json_or_yaml(activity.changes.survey_spec)

        assert spec['spec'][0]['default'] == '$encrypted$'
        assert activity.object1 == resource.type
        assert activity.object2 == ''
        assert activity.operation == 'delete'
        assert activity.object_association == ''

    def test_copying_jt_with_labels_should_not_create_activity_stream_entries_for_each_label(self, factories, admin_user):
        label_name = fauxfactory.gen_alphanumeric()
        org = factories.organization()
        jt = factories.job_template()

        # original JT has 3 labels and one associate activity stream entry each
        for i in range(3):
            jt.related.labels.post({'name': label_name + str(i), 'organization': org.id})
        assert jt.related.activity_stream.get(operation='create').count == 1
        assert jt.related.activity_stream.get(operation='associate', object2='label').count == 3

        # copied JT has 3 labels and no associate activity stream entries for the labels
        copied = jt.get_related('copy').post({'name': six.text_type('{} (Copied)').format(jt.name)})
        utils.poll_until(lambda: copied.related.labels.get().count > 0, interval=10, timeout=30)
        assert copied.related.activity_stream.get(operation='create').count == 1
        assert copied.related.activity_stream.get(operation='associate', object2='label').count == 0

    @pytest.mark.parametrize('jt_type', ['job_template', 'workflow_job_template'])
    def test_launching_template_with_labels_should_not_create_activity_stream_entries_for_each_label(self, factories, admin_user, jt_type):
        label_name = fauxfactory.gen_alphanumeric()
        org = factories.organization()
        jt = getattr(factories, jt_type)()
        actual_jt = jt

        if jt_type == 'workflow_job_template':
            actual_jt = factories.job_template()
            factories.workflow_job_template_node(
                workflow_job_template=jt,
                unified_job_template=actual_jt
            )

        # original JT has 3 labels and one associate activity stream entry each
        for i in range(3):
            actual_jt.related.labels.post({'name': label_name + str(i), 'organization': org.id})

        job = jt.launch().wait_until_completed()
        if jt_type == 'workflow_job_template':
            wfjn = job.related.workflow_nodes.get().results.pop()
            job = wfjn.get_related('job')
        assert job.related.activity_stream.get(operation='create').count == 1
        assert job.related.activity_stream.get(operation='associate', object2='label').count == 0

        relaunched = job.relaunch().wait_until_completed()
        assert relaunched.related.activity_stream.get(operation='create').count == 1
        assert relaunched.related.activity_stream.get(operation='associate', object2='label').count == 0

    @pytest.mark.parametrize('role', ['Admin', 'Read', 'Member', 'Execute', 'Notification Admin', 'Workflow Admin',
                                      'Credential Admin', 'Job Template Admin', 'Project Admin', 'Inventory Admin',
                                      'Auditor'])
    def test_entry_generated_when_org_role_associated_with_user(self, factories, role):
        org = factories.organization()
        user = factories.user()
        org.set_object_roles(user, role)

        activity = org.related.activity_stream.get().results.pop()
        assert activity.operation == 'associate'
        assert set([activity.object1, activity.object2]) == set(['organization', 'user'])
        assert set([activity.changes.object1_pk, activity.changes.object2_pk]) == set([user.id, org.id])
        assert activity.object_association == 'role'

    def assert_not_concerning(self, content):
        """Given some data in content, assures that no encrpyted content lies
        therein.
        """
        dict_content = content
        if isinstance(content, six.string_types):
            if content.startswith('$encrypted$'):
                assert len(content) == len('$encrypted$'), (
                    'The value {} appears to contain un-hidden encrypted data.'
                ).format(content)
            dict_content = None
            try:
                dict_content = json.loads(content)
            except Exception:
                try:
                    dict_content = yaml.load(content, Loader=yaml.SafeLoader)
                except Exception:
                    pass
        sub_items = []
        if isinstance(dict_content, dict):
            sub_items = [(k, v) for k, v in dict_content.items()]
        elif isinstance(dict_content, list):
            sub_items = [(i, v) for i, v in enumerate(dict_content)]
        for key, item in sub_items:
            try:
                self.assert_not_concerning(item)
            except AssertionError as e:
                raise AssertionError(
                    'In position {}: {}'.format(key, e)
                )

    @pytest.mark.yolo
    @pytest.mark.second_to_last
    def test_fish_for_sensitive_content(self, v2):
        ct = 0
        this_page = v2.activity_stream.get(changes__icontains='$encrypted$')
        lvl = 'debug'
        if this_page.count > 100000:
            lvl = 'error'
        elif this_page.count > 10000:
            lvl = 'warn'
        elif this_page.count > 1000:
            lvl = 'info'
        getattr(log, lvl)('Processing {} activity stream entries'.format(this_page.count))
        while True:
            ct += 1
            log.info('Sniffing for hazardous content in activity stream page {}'.format(ct))
            for entry in this_page.results:
                try:
                    self.assert_not_concerning(entry.changes)
                except AssertionError as e:
                    raise AssertionError(
                        '{} In entry \n{}'.format(e, entry)
                    )
            if this_page.next:
                this_page = this_page.next.get()
            else:
                break
