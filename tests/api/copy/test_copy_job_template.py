from fauxfactory import gen_boolean, gen_alpha, gen_choice, gen_integer, gen_alphanumeric
from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_Job_Template(Base_Api_Test):

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
    def test_org_admin_can_copy(self, factories, copy_with_teardown, same_org_proj, same_org_inv, set_test_roles):
        orgA = factories.v2_organization()
        orgB = factories.v2_organization()
        project = factories.v2_project(organization=orgA if same_org_proj else orgB)
        inventory = factories.v2_inventory(organization=orgA if same_org_inv else orgB)
        jt = factories.v2_job_template(inventory=inventory, project=project)
        user = factories.user()
        set_test_roles(user, orgA, 'user', 'admin')
        set_test_roles(user, jt, 'user', 'admin')

        with self.current_user(user):
            can_copy = same_org_proj and same_org_inv
            assert jt.can_copy() == can_copy

            if can_copy:
                copy_with_teardown(jt)
            else:
                with pytest.raises(exc.Forbidden):
                    jt.copy()

    def test_copy_normal(self, factories, copy_with_teardown):
        jt = factories.v2_job_template()
        new_jt = copy_with_teardown(jt)
        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)

    def test_copy_jt_with_non_default_values(self, v2, factories, copy_with_teardown):
        post_options = v2.job_templates.options().actions.POST
        job_types = dict(post_options.job_type.choices).keys()
        verbosities = dict(post_options.verbosity.choices).keys()

        min_int32 = -1 << 31
        max_int32 = 1 << 31 - 1

        jt = factories.v2_job_template(job_type=gen_choice(job_types), limit=gen_alpha(), extra_vars='{"foo":"bar"}',
                                       forks=gen_integer(min_value=0, max_value=max_int32),
                                       verbosity=gen_choice(verbosities), job_tags=gen_alpha(),
                                       force_handlers=gen_boolean(), skip_tags=gen_alpha(), start_at_task=gen_alpha(),
                                       timeout=gen_integer(min_value=min_int32, max_value=max_int32),
                                       use_fact_cache=gen_boolean(), host_config_key=gen_alphanumeric(length=32),
                                       ask_diff_mode_on_launch=gen_boolean(), ask_variables_on_launch=gen_boolean(),
                                       ask_limit_on_launch=gen_boolean(), ask_tags_on_launch=gen_boolean(),
                                       ask_skip_tags_on_launch=gen_boolean(), ask_job_type_on_launch=gen_boolean(),
                                       ask_verbosity_on_launch=gen_boolean(), ask_inventory_on_launch=gen_boolean(),
                                       ask_credential_on_launch=gen_boolean(), survey_enabled=gen_boolean(),
                                       become_enabled=gen_boolean(), diff_mode=gen_boolean(),
                                       allow_simultaneous=gen_boolean())
        new_jt = copy_with_teardown(jt)
        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)

    def test_copy_references_with_permission(self, factories, copy_with_teardown):
        vault_cred = factories.v2_credential(kind='vault', vault_password=gen_alpha())
        machine_cred = factories.v2_credential(kind='ssh')
        jt = factories.v2_job_template(credential=machine_cred, vault_credential=vault_cred.id)
        cred_ids = [cred.id for cred in jt.related.credentials.get().results]

        assert jt.vault_credential == vault_cred.id
        assert jt.credential == machine_cred.id
        assert len(cred_ids) == 2
        assert vault_cred.id in cred_ids
        assert machine_cred.id in cred_ids

        new_jt = copy_with_teardown(jt)
        new_cred_ids = [cred.id for cred in new_jt.related.credentials.get().results]
        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)
        assert new_jt.vault_credential == jt.vault_credential
        assert new_jt.credential == jt.credential
        assert sorted(new_cred_ids) == sorted(cred_ids)

    @pytest.mark.github('https://github.com/ansible/tower/issues/2263')
    def test_copy_references_without_permission(self, factories, copy_with_teardown, set_test_roles):
        orgA = factories.v2_organization()
        orgB = factories.v2_organization()
        vault_cred = factories.v2_credential(kind='vault', vault_password=gen_alpha(), organization=orgA)
        machine_cred = factories.v2_credential(kind='ssh', organization=orgA)
        project = factories.v2_project(organization=orgB)
        inventory = factories.v2_inventory(organization=orgB)
        jt = factories.v2_job_template(inventory=inventory, project=project, credential=machine_cred,
                                       vault_credential=vault_cred.id)
        user = factories.user()
        set_test_roles(user, orgB, 'user', 'admin')

        with self.current_user(user):
            new_jt = copy_with_teardown(jt)
            check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)
            new_cred_ids = [cred.id for cred in new_jt.related.credentials.get().results]
            assert not new_jt.vault_credential
            assert not new_jt.credential
            assert len(new_cred_ids) == 0

    def test_copy_jt_instance_groups(self, factories, copy_with_teardown):
        ig = factories.instance_group()
        jt = factories.v2_job_template()
        jt.add_instance_group(ig)
        new_jt = copy_with_teardown(jt)

        old_igs = jt.related.instance_groups.get()
        new_igs = new_jt.related.instance_groups.get()

        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)
        assert old_igs.count == 1
        assert new_igs.count == old_igs.count
        assert new_igs.results[0].id == old_igs.results[0].id

    def test_copy_jt_labels(self, factories, copy_with_teardown):
        jt = factories.v2_job_template()
        label = factories.v2_label()
        jt.add_label(label)
        new_jt = copy_with_teardown(jt)

        old_labels = jt.related.labels.get()
        new_labels = new_jt.related.labels.get()

        check_fields(jt, new_jt, self.identical_fields, self.unequal_fields)
        assert old_labels.count == 1
        assert new_labels.count == old_labels.count
        assert new_labels.results[0].id == old_labels.results[0].id

    def test_copy_jt_survey_spec(self, factories, copy_with_teardown):
        jt = factories.v2_job_template()
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
