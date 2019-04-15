#!/usr/bin/env python
import sys
import os
import yaml


# Allow for folded/literal yaml blocks (see
# http://stackoverflow.com/questions/6432605/any-yaml-libraries-in-python-that-support-dumping-of-long-strings-as-block-liter)
class folded(str):
    pass


def folded_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>')


class literal(str):
    pass


def literal_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')


yaml.add_representer(folded, folded_representer)


yaml.add_representer(literal, literal_representer)


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print("usage: %s <template> <output_file>" % sys.argv[0])
        sys.exit(1)

    # FIXME - support optparser parameters
    (credentials_template, credentials_file) = sys.argv[1:3]

    # Gather SCM private key credentials
    if "SCM_KEY_DATA" not in os.environ:
        os.environ["SCM_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/id_rsa.github-ansible-jenkins-nopassphrase")
    if "SCM_KEY_DATA_ENCRYPTED" not in os.environ:
        os.environ["SCM_KEY_DATA_ENCRYPTED"] = os.path.expandvars("$HOME/.ssh/id_rsa.github-ansible-jenkins-passphrase")

    # Gather SSH private key credentials
    if "SSH_KEY_DATA" not in os.environ:
        os.environ["SSH_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/id_rsa.jenkins-nopassphrase")
    if "SSH_KEY_DATA_ENCRYPTED" not in os.environ:
        os.environ["SSH_KEY_DATA_ENCRYPTED"] = os.path.expandvars("$HOME/.ssh/id_rsa.jenkins-passphrase")

    # Gather NET private key credentials
    if "NET_KEY_DATA" not in os.environ:
        os.environ["NET_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/id_rsa.network-nopassphrase")

    # Gather GCE and Azure Classic KEY_DATA
    if "GCE_KEY_DATA" not in os.environ:
        os.environ["GCE_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/google_compute_engine-3fab726444ae.pem")
    if "AZURE_CLASSIC_KEY_DATA" not in os.environ:
        os.environ["AZURE_CLASSIC_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/id_rsa.azure_classic.pem")

    # Import credentials.template
    cfg = yaml.safe_load(open(credentials_template, mode='r', encoding='utf-8'))

    # Set default admin password
    cfg['default']['password'] = os.environ.get("AWX_ADMIN_PASSWORD", "")

    # Set aws info
    for ec2 in ['aws', 'ec2']:
        cfg['cloud'][ec2]['username'] = os.environ.get("AWS_ACCESS_KEY", "")
        cfg['cloud'][ec2]['password'] = os.environ.get("AWS_SECRET_KEY", "")

    # Set gce info
    cfg['cloud']['gce']['username'] = os.environ.get("GCE_USERNAME", "")
    cfg['cloud']['gce']['project'] = os.environ.get("GCE_PROJECT", "")
    cfg['cloud']['gce']['ssh_key_data'] = literal(open(os.environ["GCE_KEY_DATA"], mode='r', encoding='utf-8').read())

    # Set azure classic info
    cfg['cloud']['azure_classic']['username'] = os.environ.get("AZURE_CLASSIC_USERNAME", "")
    cfg['cloud']['azure_classic']['ssh_key_data'] = literal(open(os.environ["AZURE_CLASSIC_KEY_DATA"], mode='r', encoding='utf-8').read())

    # Set azure info
    cfg['cloud']['azure']['subscription_id'] = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
    cfg['cloud']['azure']['client_id'] = os.environ.get("AZURE_CLIENT_ID", "")
    cfg['cloud']['azure']['secret'] = os.environ.get("AZURE_SECRET", "")
    cfg['cloud']['azure']['tenant'] = os.environ.get("AZURE_TENANT", "")

    # Set azure active directory info
    cfg['cloud']['azure_ad']['subscription_id'] = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
    cfg['cloud']['azure_ad']['ad_user'] = os.environ.get("AZURE_AD_USER", "")
    cfg['cloud']['azure_ad']['password'] = os.environ.get("AZURE_PASSWORD", "")

    # Set vmware info
    cfg['cloud']['vmware']['username'] = os.environ.get("VMWARE_USERNAME", "")
    cfg['cloud']['vmware']['password'] = os.environ.get("VMWARE_PASSWORD", "")
    cfg['cloud']['vmware']['host'] = os.environ.get("VMWARE_HOST", "")

    # Set legacy openstack info
    cfg['cloud']['openstack']['username'] = os.environ.get("OPENSTACK_USERNAME", "")
    cfg['cloud']['openstack']['password'] = os.environ.get("OPENSTACK_PASSWORD", "")
    cfg['cloud']['openstack']['host'] = os.environ.get("OPENSTACK_HOST", "")
    cfg['cloud']['openstack']['project'] = os.environ.get("OPENSTACK_PROJECT", "")

    # Set openstack_v2 info
    cfg['cloud']['openstack_v2']['username'] = os.environ.get("OPENSTACK_V2_USERNAME", "")
    cfg['cloud']['openstack_v2']['password'] = os.environ.get("OPENSTACK_V2_PASSWORD", "")
    cfg['cloud']['openstack_v2']['host'] = os.environ.get("OPENSTACK_V2_HOST", "")
    cfg['cloud']['openstack_v2']['project'] = os.environ.get("OPENSTACK_V2_PROJECT", "")

    # Set openstack_v3 info
    cfg['cloud']['openstack_v3']['username'] = os.environ.get("OPENSTACK_V3_USERNAME", "")
    cfg['cloud']['openstack_v3']['password'] = os.environ.get("OPENSTACK_V3_PASSWORD", "")
    cfg['cloud']['openstack_v3']['host'] = os.environ.get("OPENSTACK_V3_HOST", "")
    cfg['cloud']['openstack_v3']['project'] = os.environ.get("OPENSTACK_V3_PROJECT", "")
    cfg['cloud']['openstack_v3']['domain'] = os.environ.get("OPENSTACK_V3_DOMAIN", "")

    # Set SCM info
    cfg['scm']['password'] = os.environ.get("SCM_PASSWORD", "")
    cfg['scm']['ssh_key_data'] = literal(open(os.environ["SCM_KEY_DATA"], mode='r', encoding='utf-8').read())
    cfg['scm']['encrypted']['ssh_key_data'] = literal(open(os.environ["SCM_KEY_DATA_ENCRYPTED"], mode='r', encoding='utf-8').read())
    cfg['scm']['encrypted']['ssh_key_unlock'] = os.environ.get("SCM_KEY_UNLOCK", "")

    # Set SSH info
    cfg['ssh']['password'] = os.environ.get("SSH_PASSWORD", "")
    cfg['ssh']['ssh_key_data'] = literal(open(os.environ["SSH_KEY_DATA"], mode='r', encoding='utf-8').read())
    cfg['ssh']['encrypted']['ssh_key_data'] = literal(open(os.environ["SSH_KEY_DATA_ENCRYPTED"], mode='r', encoding='utf-8').read())
    cfg['ssh']['encrypted']['ssh_key_unlock'] = os.environ.get("SSH_KEY_UNLOCK", "")
    cfg['ssh']['vault_password'] = os.environ.get("VAULT_PASSWORD", "")
    cfg['ssh']['sudo_username'] = os.environ.get("SUDO_USERNAME", "")
    cfg['ssh']['sudo_password'] = os.environ.get("SUDO_PASSWORD", "")
    cfg['ssh']['su_username'] = os.environ.get("SU_USERNAME", "")
    cfg['ssh']['su_password'] = os.environ.get("SU_PASSWORD", "")
    cfg['ssh']['become_username'] = os.environ.get("BECOME_USERNAME", "")
    cfg['ssh']['become_password'] = os.environ.get("BECOME_PASSWORD", "")

    # Set network info
    cfg['network']['password'] = os.environ.get("NET_PASSWORD", "")
    cfg['network']['authorize'] = os.environ.get("NET_AUTHORIZE", "")
    cfg['network']['ssh_key_data'] = literal(open(os.environ["NET_KEY_DATA"], mode='r', encoding='utf-8').read())

    # Set github info
    cfg['github']['username'] = os.environ.get("GITHUB_USERNAME", "")
    cfg['github']['token'] = os.environ.get("GITHUB_TOKEN", "")
    cfg['github']['completed'] = os.environ.get("GITHUB_COMPLETED", "").split(' ')

    # Set e-mail service info
    cfg['notification_services']['email']['host'] = os.environ.get("EMAIL_HOST", "")
    cfg['notification_services']['email']['password'] = os.environ.get("EMAIL_PASSWORD", "")
    cfg['notification_services']['email']['port'] = int(os.environ.get("EMAIL_PORT", 25))
    # FIXME: turn this into proper list
    cfg['notification_services']['email']['recipients'] = [os.environ.get("EMAIL_RECIPIENTS", "")]
    cfg['notification_services']['email']['sender'] = os.environ.get("EMAIL_SENDER", "")
    cfg['notification_services']['email']['use_ssl'] = os.environ.get("EMAIL_USE_SSL", "").lower() == 'true'
    cfg['notification_services']['email']['use_tls'] = os.environ.get("EMAIL_USE_TLS", "").lower() == 'true'
    cfg['notification_services']['email']['username'] = os.environ.get("EMAIL_USERNAME", "")

    # Set irc service info
    cfg['notification_services']['irc']['server'] = os.environ.get("IRC_SERVER", "")
    cfg['notification_services']['irc']['port'] = int(os.environ.get("IRC_PORT", 6667))
    cfg['notification_services']['irc']['use_ssl'] = os.environ.get("IRC_USE_SSL", "").lower() == 'true'
    cfg['notification_services']['irc']['password'] = os.environ.get("IRC_PASSWORD", "")
    cfg['notification_services']['irc']['nickname'] = os.environ.get("IRC_NICKNAME", "")
    # FIXME: Turn into proper list
    cfg['notification_services']['irc']['targets'] = [os.environ.get("IRC_TARGETS", "")]

    # Set pagerduty service info
    cfg['notification_services']['pagerduty']['client_name'] = os.environ.get("PAGERDUTY_CLIENT_NAME", "")
    cfg['notification_services']['pagerduty']['service_key'] = os.environ.get("PAGERDUTY_SERVICE_KEY", "")
    cfg['notification_services']['pagerduty']['subdomain'] = os.environ.get("PAGERDUTY_SUBDOMAIN", "")
    cfg['notification_services']['pagerduty']['token'] = os.environ.get("PAGERDUTY_TOKEN", "")

    # Set slack service info
    cfg['notification_services']['slack']['channels'] = [os.environ.get("SLACK_CHANNELS", "")]
    cfg['notification_services']['slack']['token'] = os.environ.get("SLACK_TOKEN", "")

    # Set twilio service info
    cfg['notification_services']['twilio']['account_sid'] = os.environ.get("TWILIO_ACCOUNT_SID", "")
    cfg['notification_services']['twilio']['account_token'] = os.environ.get("TWILIO_ACCOUNT_TOKEN", "")
    cfg['notification_services']['twilio']['from_number'] = os.environ.get("TWILIO_FROM_NUMBER", "")
    cfg['notification_services']['twilio']['to_numbers'] = [os.environ.get("TWILIO_TO_NUMBERS", "")]

    # Set webhook service info
    cfg['notification_services']['webhook']['url'] = os.environ.get("WEBHOOK_URL", "")
    # FIXME: Update with new fields
    cfg['notification_services']['webhook']['gce_project'] = os.environ.get("WEBHOOK_PROJECT", "")
    cfg['notification_services']['webhook']['gce_parent_key'] = os.environ.get("WEBHOOK_PARENT_KEY", "")
    cfg['notification_services']['webhook']['gce_body_field'] = os.environ.get("WEBHOOK_BODY_FIELD", "")
    cfg['notification_services']['webhook']['gce_headers_field'] = os.environ.get("WEBHOOK_HEADERS_FIELD", "")

    yaml.dump(cfg, open(credentials_file, mode='w+', encoding='utf-8'))
