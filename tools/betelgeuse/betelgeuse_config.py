PARAMETRIZE_DECORATOR = 'pytest.mark.parametrize'

TOWER_REQUIREMENTS = [
    'Auth',
    'Cluster',
    'Copy',
    'Credentials',
    'External Data',
    'External Logging',
    'Inventories',
    'Jobs',
    'Job Templates',
    'Notification Templates',
    'RBAC',
    'Schedules',
    'Security',
    'Services',
    'Settings',
    'Activity Stream',
    'Ad hoc Commands',
    'Channels',
    'Custom Virtualenv',
    'Fact Cache',
    'Labels',
    'Named URLs',
    'Notifications',
    'Pagination',
    'Projects',
    'Prompts',
    'Task Manager',
    'Tower Modules',
    'Workflows',
    'License',
    'Miscellaneous',
    'Upgrade',
]


def get_caseimportance_value(testcase):
    decorators = testcase.decorators + (testcase.class_decorators or [])
    marks = [
        'pytest.mark.ansible_integration',
        'pytest.mark.yolo',
    ]
    for mark in marks:
        if mark in decorators:
            return 'critical'
    return 'medium'


def get_description_value(testcase):
    return testcase.name


def get_parametrized_value(testcase):
    if testcase.junit_id in DYNAMIC_PARAMETRIZED_TESTS:
        return 'yes'
    class_decorators = testcase.class_decorators or []
    for decorator in testcase.decorators + class_decorators:
        if decorator.startswith(PARAMETRIZE_DECORATOR):
            return 'yes'
    return 'no'


def get_requirement_value(testcase):
    if testcase.testmodule.startswith('tests/cli'):
        return 'CLI'

    if testcase.testmodule.startswith('tests/license'):
        return 'License'

    if testcase.testmodule.startswith('tests/upgrade'):
        return 'Upgrade'

    if testcase.testmodule.startswith('tests/api'):
        requirement = testcase.testmodule.split('/')[2]
        requirement = requirement.replace('test_', '').replace('.py', '')
        requirement = requirement.replace('_', ' ').title()

        # Adjust to some requirement names
        requirement = requirement.replace('Ad Hoc', 'Ad hoc')
        requirement = requirement.replace('Named Urls', 'Named URLs')
        requirement = requirement.replace('Rbac', 'RBAC')

        if requirement not in TOWER_REQUIREMENTS:
            return 'Miscellaneous'
        return requirement


DEFAULT_APPROVERS_VALUE = 'ansible_machine:approved'
DEFAULT_ASSIGNEE_VALUE = 'ansible_machine'
DEFAULT_CASEIMPORTANCE_VALUE = get_caseimportance_value
DEFAULT_DESCRIPTION_VALUE = get_description_value
DEFAULT_PARAMETRIZED_VALUE = get_parametrized_value
DEFAULT_REQUIREMENT_VALUE = get_requirement_value
DEFAULT_STATUS_VALUE = 'approved'


DYNAMIC_PARAMETRIZED_TESTS = (
    'tests.api.auth.test_application_tokens.TestApplications.test_application_creation_in_activity_stream',
    'tests.api.auth.test_application_tokens.TestApplications.test_application_deletion_in_activity_stream',
    'tests.api.auth.test_application_tokens.TestApplications.test_application_modification_in_activity_stream',
    'tests.api.auth.test_application_tokens.TestApplicationTokens.test_token_creation_in_activity_stream',
    'tests.api.auth.test_application_tokens.TestApplicationTokens.test_token_modification_in_activity_stream',
    'tests.api.copy.test_copy_inventory.Test_Copy_Inventory.test_copy_inventory_with_sources',
    'tests.api.external_data.test_metrics.TestMetrics.test_metrics_readable_by_system_user',
    'tests.api.external_data.test_metrics.TestMetrics.test_metrics_unreadable_by_org_users',
    'tests.api.external_data.test_metrics.TestMetrics.test_metrics_unreadable_by_unprivileged_user',
    'tests.api.inventories.test_cloud_inventory_update.TestCloudInventoryUpdate.test_cloud_update_with_populated_source_region',
    'tests.api.inventories.test_cloud_inventory_update.TestCloudInventoryUpdate.test_cloud_update_with_source_region',
    'tests.api.inventories.test_cloud_inventory_update.TestCloudInventoryUpdate.test_cloud_update_with_unpopulated_source_region',
    'tests.api.inventories.test_cloud_inventory_update.TestCloudInventoryUpdate.test_update_cloud_inventory_source',
    'tests.api.inventories.test_group.TestGroup.test_associate_with_non_root_group',
    'tests.api.inventories.test_group.TestGroup.test_associate_with_root_group',
    'tests.api.inventories.test_group.TestGroup.test_delete',
    'tests.api.inventories.test_group.TestGroup.test_disassociate_non_root_group',
    'tests.api.inventories.test_group.TestGroup.test_disassociate_root_group',
    'tests.api.inventories.test_group.TestGroup.test_reassociate_with_non_root_group',
    'tests.api.inventories.test_inventory_scripts.Test_Inventory_Scripts.test_delete_as_privileged_user',
    'tests.api.inventories.test_inventory_scripts.Test_Inventory_Scripts.test_delete_as_unprivileged_user',
    'tests.api.inventories.test_inventory_scripts.Test_Inventory_Scripts.test_get_as_privileged_user',
    'tests.api.inventories.test_inventory_scripts.Test_Inventory_Scripts.test_import_script_failure',
    'tests.api.inventories.test_inventory_scripts.Test_Inventory_Scripts.test_post_as_privileged_user',
    'tests.api.inventories.test_inventory_scripts.Test_Inventory_Scripts.test_post_as_unprivileged_user',
    'tests.api.inventories.test_scm_inventory_source.TestSCMInventorySource.test_custom_credential_affects_ansible_env_of_scm_inventory',
    'tests.api.inventories.test_scm_inventory_source.TestSCMInventorySource.test_scm_inventory_groups_and_group_vars',
    'tests.api.inventories.test_scm_inventory_source.TestSCMInventorySource.test_scm_inventory_hosts_and_host_vars',
    'tests.api.jobs.test_jobs.Test_Job_Env.test_job_env_variables_contains_utf8',
    'tests.api.jobs.test_jobs.Test_Job_Env.test_job_env_with_cloud_credential',
    'tests.api.jobs.test_jobs.Test_Job_Env.test_job_env_with_network_credential',
    'tests.api.jobs.test_jobs.Test_Job.test_cancel_pending_job',
    'tests.api.jobs.test_jobs.Test_Job.test_cancel_running_job',
    'tests.api.jobs.test_jobs.Test_Job.test_jobs_persist_beyond_job_template_deletion',
    'tests.api.jobs.test_jobs.Test_Job.test_other_users_cannot_relaunch_orphan_jobs',
    'tests.api.jobs.test_jobs.Test_Job.test_relaunch_uses_extra_vars_from_job',
    'tests.api.jobs.test_jobs.Test_Job.test_relaunch_with_deleted_related',
    'tests.api.jobs.test_jobs.Test_Job.test_relaunch_with_multi_ask_credential_and_passwords_in_payload',
    'tests.api.jobs.test_jobs.Test_Job.test_relaunch_with_multi_ask_credential_and_without_passwords',
    'tests.api.jobs.test_jobs.Test_Job.test_urls_are_sanitized_in_job_env',
    'tests.api.jobs.test_system_jobs.Test_System_Jobs.test_cleanup_jobs',
    'tests.api.jobs.test_system_jobs.Test_System_Jobs.test_method_not_allowed',
    'tests.api.jobs.test_system_job_templates.Test_System_Job_Template.test_launch_as_non_superuser',
    'tests.api.jobs.test_system_job_templates.Test_System_Job_Template.test_launch_as_superuser',
    'tests.api.jobs.test_system_job_templates.Test_System_Job_Template.test_launch_with_extra_vars',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_assignment_of_host_config_key',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_matching_hosts_contains_member_in_member_query',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_provision_failure_with_currently_running_and_simultaneous_disallowed',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_provision_failure_with_incorrect_hostkey',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_provision_failure_with_null_inventory',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_provision_failure_without_inventory',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_provision_job_template_with_limit',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_provision_without_required_extra_vars',
    'tests.api.job_templates.test_job_template_callbacks.TestJobTemplateCallbacks.test_provision_with_split_job',
    'tests.api.job_templates.test_job_template_credentials.TestJobTemplateExtraCredentials.test_job_template_with_added_and_removed_custom_extra_credentials',
    'tests.api.job_templates.test_job_template_credentials.TestJobTemplateLaunchCredentials.test_launch_with_encrypted_ssh_credential',
    'tests.api.job_templates.test_job_template_credentials.TestJobTemplateLaunchCredentials.test_launch_with_unencrypted_ssh_credential',
    'tests.api.job_templates.test_job_template_credentials.TestJobTemplateRelatedCredentials.test_add_extra_credentials_check_related_credentials',
    'tests.api.job_templates.test_job_template_extra_vars.TestJobTemplateExtraVars.test_launch_with_ask_variables_on_launch',
    'tests.api.job_templates.test_job_template_extra_vars.TestJobTemplateExtraVars.test_launch_with_excluded_variables_in_payload',
    'tests.api.job_templates.test_job_template_extra_vars.TestJobTemplateExtraVars.test_launch_with_extra_vars_at_launch',
    'tests.api.job_templates.test_job_template_extra_vars.TestJobTemplateExtraVars.test_launch_with_extra_vars_from_job_template',
    'tests.api.job_templates.test_job_template_extra_vars.TestJobTemplateExtraVars.test_launch_with_variables_needed_to_start_and_extra_vars_at_launch',
    'tests.api.job_templates.test_job_templates.TestJobTemplates.test_conflict_exception_with_running_job',
    'tests.api.job_templates.test_job_templates.TestJobTemplates.test_launch_check_job_template',
    'tests.api.job_templates.test_job_templates.TestJobTemplates.test_launch_template_with_deleted_related',
    'tests.api.job_templates.test_job_templates.TestJobTemplates.test_launch_with_ignored_payload',
    'tests.api.job_templates.test_job_templates.TestJobTemplates.test_launch_with_inventory_in_payload',
    'tests.api.job_templates.test_job_templates.TestJobTemplates.test_launch_with_limit_in_payload',
    'tests.api.job_templates.test_job_templates.TestJobTemplates.test_launch_with_unmatched_limit_value',
    'tests.api.notification_templates.test_common.Test_Common_NotificationTemplate.test_job_template_launch_use_default_message_when_messages_is_missing',
    'tests.api.notification_templates.test_common.Test_Common_NotificationTemplate.test_notification_template_contains_update_all_default_messages',
    'tests.api.notification_templates.test_common.Test_Common_NotificationTemplate.test_notification_template_contains_update_some_default_messages',
    'tests.api.notification_templates.test_common.Test_Common_NotificationTemplate.test_notification_template_default_contains_no_message',
    'tests.api.notification_templates.test_common.Test_Common_NotificationTemplate.test_notification_template_fails_when_providing_invalid_payload',
    'tests.api.rbac.test_config.TestConfigUserAccess.test_privileged_user',
    'tests.api.rbac.test_config.TestConfigUserAccess.test_unprivileged_user',
    'tests.api.rbac.test_credential_types_rbac.TestCredentialTypesRBAC.test_non_superuser_cannot_create_credential_type',
    'tests.api.rbac.test_credential_types_rbac.TestCredentialTypesRBAC.test_non_superusers_can_see_credential_types',
    'tests.api.rbac.test_inventories_rbac.TestInventoryRBAC.test_cloud_source_credential_reassignment',
    'tests.api.rbac.test_job_templates_rbac.Test_Job_Template_RBAC.test_relaunch_with_ask_inventory',
    'tests.api.rbac.test_license_rbac.Test_License_RBAC.test_delete_as_non_superuser',
    'tests.api.rbac.test_license_rbac.Test_License_RBAC.test_post_as_non_superuser',
    'tests.api.rbac.test_notifications_rbac.Test_Notifications_RBAC.test_notification_read_as_unprivileged_user',
    'tests.api.rbac.test_notifications_rbac.Test_Notifications_RBAC.test_notification_test_as_unprivileged_user',
    'tests.api.rbac.test_notification_templates_rbac.Test_Notification_Template_RBAC.test_notification_template_associate_as_org_admin',
    'tests.api.rbac.test_notification_templates_rbac.Test_Notification_Template_RBAC.test_notification_template_associate_as_unprivileged_user',
    'tests.api.rbac.test_notification_templates_rbac.Test_Notification_Template_RBAC.test_notification_template_create_as_unprivileged_user',
    'tests.api.rbac.test_notification_templates_rbac.Test_Notification_Template_RBAC.test_notification_template_delete_as_unprivileged_user',
    'tests.api.rbac.test_notification_templates_rbac.Test_Notification_Template_RBAC.test_notification_template_edit_as_unprivileged_user',
    'tests.api.rbac.test_notification_templates_rbac.Test_Notification_Template_RBAC.test_notification_template_read_as_unprivileged_user',
    'tests.api.rbac.test_organizations.Test_Organizations.test_organization_related_counts',
    'tests.api.rbac.test_relaunch_ask_rbac.TestRelaunchAskRBAC.test_relaunch_with_credentials_allowed',
    'tests.api.rbac.test_relaunch_ask_rbac.TestRelaunchAskRBAC.test_relaunch_with_survey_passwords_forbidden',
    'tests.api.rbac.test_schedules_rbac.Test_Schedules_RBAC.test_crud_as_org_admin',
    'tests.api.rbac.test_schedules_rbac.Test_Schedules_RBAC.test_crud_as_org_user',
    'tests.api.rbac.test_schedules_rbac.Test_Schedules_RBAC.test_crud_as_superuser',
    'tests.api.rbac.test_schedules_rbac.Test_Schedules_RBAC.test_schedule_reassignment',
    'tests.api.rbac.test_schedules_rbac.Test_Schedules_RBAC.test_user_capabilities_as_org_admin',
    'tests.api.rbac.test_schedules_rbac.Test_Schedules_RBAC.test_user_capabilities_as_superuser',
    'tests.api.rbac.test_settings_rbac.TestSettingsRBAC.test_delete_nested_endpoint_as_non_superuser',
    'tests.api.rbac.test_settings_rbac.TestSettingsRBAC.test_edit_nested_endpoint_as_non_superuser',
    'tests.api.rbac.test_settings_rbac.TestSettingsRBAC.test_get_main_endpoint_as_non_superuser',
    'tests.api.rbac.test_settings_rbac.TestSettingsRBAC.test_get_nested_endpoint_as_non_superuser',
    'tests.api.rbac.test_system_jobs_rbac.TestSystemJobRBAC.test_cannot_launch_as_system_auditor',
    'tests.api.rbac.test_system_jobs_rbac.TestSystemJobRBAC.test_get_detail_view_as_non_superuser',
    'tests.api.rbac.test_system_jobs_rbac.TestSystemJobRBAC.test_get_detail_view_as_superuser',
    'tests.api.rbac.test_teams.Test_Teams.test_non_superuser_cannot_create_team_in_another_organization',
    'tests.api.rbac.test_teams.Test_Teams.test_privileged_user_can_create_team',
    'tests.api.rbac.test_teams.Test_Teams.test_unprivileged_user_cannot_create_team',
    'tests.api.rbac.test_users.Test_Users.test_non_superuser_cannot_elevate_themselves_to_superuser',
    'tests.api.rbac.test_users.Test_Users.test_nonsuperusers_cannot_create_orphaned_user',
    'tests.api.schedules.test_schedules.TestSchedules.test_duplicate_schedules_disallowed',
    'tests.api.schedules.test_schedules.TestSchedules.test_invalid_rrules_are_rejected',
    'tests.api.schedules.test_schedules.TestSchedules.test_new_resources_are_without_schedules',
    'tests.api.schedules.test_schedules.TestSchedules.test_only_count_limited_future_recurrences_are_evaluated',
    'tests.api.schedules.test_schedules.TestSchedules.test_only_count_limited_overlapping_recurrences_are_evaluated',
    'tests.api.schedules.test_schedules.TestSchedules.test_only_count_limited_previous_recurrencences_are_evaluated',
    'tests.api.schedules.test_schedules.TestSchedules.test_only_until_limited_future_recurrences_are_evaluated',
    'tests.api.schedules.test_schedules.TestSchedules.test_only_until_limited_previous_recurrencences_are_evaluated',
    'tests.api.schedules.test_schedules.TestSchedules.test_schedule_basic_integrity',
    'tests.api.schedules.test_schedules.TestSchedules.test_schedule_triggers_launch_with_count',
    'tests.api.schedules.test_schedules.TestSchedules.test_schedule_triggers_launch_without_count',
    'tests.api.schedules.test_schedules.TestSchedules.test_successful_cascade_schedule_deletions',
    'tests.api.schedules.test_schedules.TestSchedules.test_successful_schedule_deletions',
    'tests.api.schedules.test_system_job_template_schedules.TestSystemJobTemplateSchedules.test_sjt_can_have_multiple_schedules',
    'tests.api.settings.test_auth.Test_Auth.test_updated_entries',
    'tests.api.settings.test_ldap.TestLDAP.test_ldap_is_superuser_supercedes_is_system_auditor',
    'tests.api.settings.test_main.TestGeneralSettings.test_reset_setting',
    'tests.api.settings.test_main.TestGeneralSettings.test_stdout_max_bytes_display',
    'tests.api.settings.test_proot.Test_Proot.test_ssh_connections',
    'tests.api.test_ad_hoc_commands.Test_Ad_Hoc_Commands_Main.test_launch_with_ask_credential_and_invalid_passwords_in_payload',
    'tests.api.test_ad_hoc_commands.Test_Ad_Hoc_Commands_Main.test_launch_with_ask_credential_and_passwords_in_payload',
    'tests.api.test_ad_hoc_commands.Test_Ad_Hoc_Commands_Main.test_launch_with_ask_credential_and_without_passwords_in_payload',
    'tests.api.test_ad_hoc_commands.Test_Ad_Hoc_Commands_Main.test_relaunch_command_with_ask_credential_and_passwords',
    'tests.api.test_ad_hoc_commands.Test_Ad_Hoc_Commands_Main.test_relaunch_command_with_ask_credential_and_without_passwords',
    'tests.api.test_ad_hoc_commands.Test_Ad_Hoc_Commands_Main.test_relaunch_with_deleted_related',
    'tests.api.test_labels.Test_Labels.test_filter_by_label_name',
    'tests.api.test_labels.Test_Labels.test_job_association',
    'tests.api.test_labels.Test_Labels.test_job_label_persistence',
    'tests.api.test_labels.Test_Labels.test_job_reference_delete',
    'tests.api.test_labels.Test_Labels.test_job_template_association',
    'tests.api.test_labels.Test_Labels.test_job_template_disassociation',
    'tests.api.test_labels.Test_Labels.test_reference_delete_with_job_template_deletion',
    'tests.api.test_labels.Test_Labels.test_reference_delete_with_job_template_disassociation',
    'tests.api.test_labels.Test_Labels.test_summary_field_label_max',
    'tests.api.test_labels.Test_Labels.test_summary_field_label_order',
    'tests.api.test_notifications.Test_Notifications.test_test_notification',
    'tests.api.test_task_manager.Test_Autospawned_Jobs.test_inventory_multiple',
    'tests.api.test_task_manager.Test_Sequential_Jobs.test_job_template',
    'tests.api.test_task_manager.Test_Sequential_Jobs.test_job_template_with_allow_simultaneous',
    'tests.api.test_task_manager.Test_Sequential_Jobs.test_related_project_update',
    'tests.api.workflows.test_combined_workflow_features.TestCombinedWorkflowFeatures.test_set_stats_propagate_correctly_through_workflow',
    'tests.api.workflows.test_workflow_approval_nodes.TestWorkflowApprovalNodes.test_approval_node_happy_path',
    'tests.api.workflows.test_workflow_convergence.Test_Workflow_Convergence.test_convergence_nodes_merge_set_stats_variables',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_artifacts_passed_to_workflow_nodes',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_extra_vars_passed_with_wfjt_when_encrypted_keywords_supplied_at_launch',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_launch_vars_passed_with_wfjt_when_launch_vars_and_multiple_surveys_present',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_launch_with_job_template_and_job_template_survey_extra_vars',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_launch_with_job_template_extra_vars',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_launch_with_workflow_and_job_template_and_both_survey_extra_vars',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_launch_with_workflow_and_job_template_extra_vars',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_launch_with_workflow_extra_vars',
    'tests.api.workflows.test_workflow_extra_vars.TestWorkflowExtraVars.test_wfjt_nodes_source_variables_with_set_stats',
    'tests.api.workflows.test_workflow_job_template_surveys.TestWorkflowJobTemplateSurveys.test_null_wfjt_survey_defaults_passed_to_jobs',
    'tests.api.workflows.test_workflow_job_template_surveys.TestWorkflowJobTemplateSurveys.test_only_select_wfjt_survey_fields_editable',
    'tests.api.workflows.test_workflow_job_template_surveys.TestWorkflowJobTemplateSurveys.test_survey_variables_overriden_when_supplied_at_launch',
    'tests.api.workflows.test_workflow_job_template_surveys.TestWorkflowJobTemplateSurveys.test_wfjt_and_wfjn_jt_survey_password_defaults_passed_to_jobs',
    'tests.api.workflows.test_workflow_job_template_surveys.TestWorkflowJobTemplateSurveys.test_wfjt_survey_with_required_and_optional_fields',
    'tests.license.test_crawler.test_authenticated',
    'tests.license.test_crawler.test_unauthenticated',
    'tests.license.test_enterprise_license.TestEnterpriseLicenseExpired.test_system_job_launch',
)
