import logging

import fauxfactory
from towerkit import utils
import towerkit.exceptions
import pytest
import six

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestActivityStream(Base_Api_Test):

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
                raise(Exception("Unprivileged user has access to unexpected activity stream content."))

    def test_inventory_id_in_group_activity_stream(self, factories):
        """Confirms that inventory_id is included in the group summary_fields for all non-delete operations"""
        inventory = factories.inventory()
        group = factories.group(inventory=inventory)
        host = factories.host(inventory=inventory)

        group.name = "UpdatedGroupName"
        with pytest.raises(towerkit.exceptions.NoContent):
            group.get_related('hosts').post(dict(associate=True, id=host.id))
        with pytest.raises(towerkit.exceptions.NoContent):
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

    @pytest.mark.github('https://github.com/ansible/tower/issues/1722')
    def test_copying_jt_with_labels_should_not_create_activity_stream_entries_for_each_label(self, v2, factories, admin_user):
        label_name = fauxfactory.gen_alphanumeric()
        org = factories.v2_organization()
        jt = factories.v2_job_template()

        # original JT has 3 labels and one associate activity stream entry each
        for i in range(3):
            jt.related.labels.post({'name': label_name + str(i), 'organization': org.id})
        assert jt.related.activity_stream.get(operation='create').count == 1
        assert jt.related.activity_stream.get(operation='associate', object2='label').count == 3

        # copied JT has 3 labels and no associate activity stream entries for the labels
        copied = jt.get_related('copy').post({'name': six.text_type('{} (Copied)').format(jt.name)})
        utils.poll_until(lambda: copied.related.labels.count > 0, interval=10, timeout=30)
        assert copied.related.activity_stream.get(operation='create').count == 1
        assert copied.related.activity_stream.get(operation='associate', object2='label').count == 0
