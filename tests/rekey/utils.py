import pprint


CLIENT_SECRET_CMD = (
    'echo "'
    'from __future__ import print_function; '
    'from awx.main.models.oauth import OAuth2Application; '
    'print(OAuth2Application.objects.filter(id={application_id}).first().client_secret)'
    '" | awx-manage shell'
)

CREDENTIAL_PASSWORD_CMD = (
    'echo "'
    'from __future__ import print_function; '
    'from awx.main.models.credential import Credential; '
    'print(Credential.objects.filter(id={credential_id}).first().get_input(\'password\'))'
    '" | awx-manage shell'
)

JOB_TEMPLATE_EXTRA_VARS_CMD = (
    'echo "'
    'from __future__ import print_function; '
    'from awx.main.models.jobs import JobTemplate; '
    'jt = JobTemplate.objects.filter(id={job_template_id}).first(); '
    'print(jt.jobs.all().first().decrypted_extra_vars())'
    '" | awx-manage shell'
)

JOB_TEMPLATE_JOB_EXTRA_VARS_CMD = (
    'echo "'
    'from __future__ import print_function; '
    'from awx.main.models.jobs import JobTemplate; '
    'jt = JobTemplate.objects.filter(id={job_template_id}).first(); '
    'print(jt.create_unified_job().decrypted_extra_vars())'
    '" | awx-manage shell'
)

WORKFLOW_JOB_TEMPLATE_EXTRA_VARS_CMD = (
    'echo "'
    'from __future__ import print_function; '
    'from awx.main.models.workflow import WorkflowJobTemplate; '
    'wfjt = WorkflowJobTemplate.objects.filter(id={workflow_job_template_id}).first(); '
    'print(wfjt.unifiedjob_unified_jobs.first().decrypted_extra_vars())'
    '" | awx-manage shell'
)

WORKFLOW_JOB_TEMPLATE_JOB_EXTRA_VARS_CMD = (
    'echo "'
    'from __future__ import print_function; '
    'from awx.main.models.workflow import WorkflowJobTemplate; '
    'wfjt = WorkflowJobTemplate.objects.filter(id={workflow_job_template_id}).first(); '
    'print(wfjt.create_unified_job().decrypted_extra_vars())'
    '" | awx-manage shell'
)

NOTIFICATION_TOKEN_CMD = (
    'echo "'
    'from __future__ import print_function; '
    'from awx.main.utils.encryption import decrypt_field; '
    'from awx.main.models.notifications import NotificationTemplate; '
    'nt = NotificationTemplate.objects.filter(id={notification_id}).first(); '
    'print(decrypt_field(nt, \'notification_configuration\', \'token\'))'
    '" | awx-manage shell'
)

SECRET_KEY_DOCKER_CMD = (
    'cat /awx_devel/awx/settings/local_settings.py '
    '| grep SECRET_KEY'
)

SECRET_KEY_CMD = 'cat /etc/tower/SECRET_KEY'

SETTINGS_CMD = (
    'echo "'
    'from __future__ import print_function; '
    'from django.conf import settings; '
    'print(settings.{setting})'
    '" | awx-manage shell'
)


def adhoc_cmd(ansible_adhoc, cmd, **kwargs):
    results = ansible_adhoc.tower.shell(
        cmd.format(**kwargs)
    )
    contacted_formated = pprint.pformat(results.contacted)
    assert all(result['rc'] == 0 for result in results.values()), contacted_formated
    expected = results.values()[0]['stdout']
    assert all(result['stdout'] == expected for result in results.values()), contacted_formated
    return expected.strip()


def fetch_secret_key(ansible_adhoc, is_docker):
    if is_docker:
        return adhoc_cmd(ansible_adhoc, SECRET_KEY_DOCKER_CMD)
    return adhoc_cmd(ansible_adhoc, SECRET_KEY_CMD)
