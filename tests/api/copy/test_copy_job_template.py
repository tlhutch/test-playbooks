from towerkit import exceptions as exc
import pytest

from tests.api import APITest
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_Job_Template(APITest):

    identical_fields = ['type', 'description', 'job_type', 'inventory', 'project', 'playbook', 'forks', 'limit',
                        'verbosity', 'extra_vars', 'job_tags', 'force_handlers', 'skip_tags', 'start_at_task',
                        'timeout', 'use_fact_cache', 'host_config_key', 'ask_diff_mode_on_launch',
                        'ask_variables_on_launch', 'ask_limit_on_launch', 'ask_tags_on_launch',
                        'ask_skip_tags_on_launch', 'ask_job_type_on_launch', 'ask_verbosity_on_launch',
                        'ask_inventory_on_launch', 'ask_credential_on_launch', 'survey_enabled', 'become_enabled',
                        'diff_mode', 'allow_simultaneous', 'custom_virtualenv']
    unequal_fields = ['id', 'created', 'modified']

    @pytest.mark.parametrize("same_org_proj", [True, False], ids=['same_org_proj', 'another_org_proj'])
    @pytest.mark.parametrize("same_org_inv", [True, False], ids=['same_org_inv', 'another_org_inv'])
    def test_org_admin_can_copy(self, factories, copy_with_teardown, same_org_proj, same_org_inv):
        orgA, orgB = [factories.organization() for _ in range(2)]
        project = factories.project(organization=orgA if same_org_proj else orgB)
        inventory = factories.inventory(organization=orgA if same_org_inv else orgB)
        jt = factories.job_template(inventory=inventory, project=project)
        user = factories.user()
        orgA.set_object_roles(user, 'admin')
        jt.set_object_roles(user, 'admin')

        with self.current_user(user):
            can_copy = same_org_proj and same_org_inv
            assert jt.can_copy() == can_copy

            if can_copy:
                copy_with_teardown(jt)
            else:
                with pytest.raises(exc.Forbidden):
                    copy_with_teardown(jt)

    def test_copy_normal(self, factories, copy_with_teardown):
        jt = factories.job_template()
        new_jt = copy_with_teardown(jt)
        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)

    def test_copy_jt_with_non_default_values(self, factories, job_template_with_random_attributes, copy_with_teardown):
        new_jt = copy_with_teardown(job_template_with_random_attributes)
        check_fields(job_template_with_random_attributes, new_jt, self.identical_fields, self.unequal_fields)

    def test_copy_jt_instance_groups(self, factories, copy_with_teardown):
        ig = factories.instance_group()
        jt = factories.job_template()
        jt.add_instance_group(ig)
        new_jt = copy_with_teardown(jt)

        old_igs = jt.related.instance_groups.get()
        new_igs = new_jt.related.instance_groups.get()

        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)
        assert old_igs.count == 1
        assert new_igs.count == old_igs.count
        assert new_igs.results[0].id == old_igs.results[0].id

    def test_copy_jt_labels(self, factories, copy_with_teardown):
        jt = factories.job_template()
        label = factories.label()
        jt.add_label(label)
        new_jt = copy_with_teardown(jt)

        old_labels = jt.related.labels.get()
        new_labels = new_jt.related.labels.get()

        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)
        assert old_labels.count == 1
        assert new_labels.count == old_labels.count
        assert new_labels.results[0].id == old_labels.results[0].id

    @pytest.mark.yolo
    def test_copy_jt_survey_spec(self, factories, copy_with_teardown):
        jt = factories.job_template()
        survey = [dict(required=False,
                       question_name='Test-1',
                       variable='var1',
                       type='password',
                       default='var1_default')]
        jt.add_survey(spec=survey)
        new_jt = copy_with_teardown(jt)

        old_survey = jt.related.survey_spec.get().json
        new_survey = new_jt.related.survey_spec.get().json

        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)
        assert new_survey == old_survey
