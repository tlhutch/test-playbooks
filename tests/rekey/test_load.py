import yaml
import fauxfactory

from . import utils


def test_rekey_load(factories, is_docker, session_ansible_adhoc, update_setting_pg, v2):
    ansible_adhoc = session_ansible_adhoc()
    password = 'rekey-{}'.format(fauxfactory.gen_alphanumeric())
    cred_type = v2.credential_types.get(kind='ssh', managed_by_tower=True).results.pop()
    survey_spec = [{
        'default': password,
        'question_name': 'What is the secret?',
        'required': False,
        'type': 'password',
        'variable': 'secret_key',
    }]

    cred = factories.credential(
        credential_type=cred_type,
        inputs={'password': password},
    )

    jt = factories.job_template()
    jt.add_survey(spec=survey_spec)
    jt.launch().wait_until_completed().assert_successful()

    wfjt = factories.workflow_job_template()
    factories.workflow_job_template_node(
        workflow_job_template=wfjt,
        unified_job_template=jt,
    )
    wfjt.add_survey(spec=survey_spec)
    wfjt.launch().wait_until_completed().assert_successful()

    update_setting_pg(
        v2.settings.get().get_endpoint('system'),
        {'REDHAT_PASSWORD': password},
    )

    token = factories.access_token(oauth_2_application=True)
    application = token.get_related('application')
    nt = factories.notification_template(
        notification_type='slack',
        notification_configuration={
            'token': password,
            'channels': ['#general']
        },
    )

    rekey_data = {
        'secret_key': utils.fetch_secret_key(ansible_adhoc, is_docker),
        'password': password,
        'application': {
            'id': application.id,
            'client_secret': utils.adhoc_cmd(
                ansible_adhoc,
                utils.CLIENT_SECRET_CMD,
                application_id=application.id
            )
        },
        'credential': {
            'id': cred.id,
            'password': password
        },
        'notification': {
            'id': nt.id,
            'token': password
        },
        'job_template': {
            'id': jt.id,
            'decrypted_extra_vars': utils.adhoc_cmd(
                ansible_adhoc,
                utils.JOB_TEMPLATE_EXTRA_VARS_CMD,
                job_template_id=jt.id
            ),
            'job_decrypted_extra_vars': utils.adhoc_cmd(
                ansible_adhoc,
                utils.JOB_TEMPLATE_JOB_EXTRA_VARS_CMD,
                job_template_id=jt.id
            )
        },
        'workflow_job_template': {
            'id': wfjt.id,
            'decrypted_extra_vars': utils.adhoc_cmd(
                ansible_adhoc,
                utils.WORKFLOW_JOB_TEMPLATE_EXTRA_VARS_CMD,
                workflow_job_template_id=wfjt.id
            ),
            'job_decrypted_extra_vars': utils.adhoc_cmd(
                ansible_adhoc,
                utils.WORKFLOW_JOB_TEMPLATE_JOB_EXTRA_VARS_CMD,
                workflow_job_template_id=wfjt.id
            )
        }
    }

    with open('rekey-data.yml', 'w') as handler:
        yaml.safe_dump(rekey_data, handler)
