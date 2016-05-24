#!/usr/bin/env python
import sys
import os
import yaml


# Allow for folded/literal yaml blocks (see
# http://stackoverflow.com/questions/6432605/any-yaml-libraries-in-python-that-support-dumping-of-long-strings-as-block-liter)
class folded(unicode):
    pass


def folded_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')


class literal(unicode):
    pass


def literal_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')


yaml.add_representer(folded, folded_representer)


yaml.add_representer(literal, literal_representer)


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print "usage: %s <template> <output_file>" % sys.argv[0]
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

    # Gather GCE and Azure KEY_DATA
    if "GCE_KEY_DATA" not in os.environ:
        os.environ["GCE_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/google_compute_engine-3fab726444ae.pem")
    if "AZURE_KEY_DATA" not in os.environ:
        os.environ["AZURE_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/id_rsa.azure.pem")

    # Import credentials.template
    cfg = yaml.load(open(credentials_template, 'r'))

    # Set default admin password
    cfg['default']['password'] = os.environ["AWX_ADMIN_PASSWORD"]

    # Set rackspace info
    for rax in ['rackspace', 'rax']:
        cfg['cloud'][rax]['username'] = os.environ["RAX_USERNAME"]
        cfg['cloud'][rax]['password'] = os.environ["RAX_API_KEY"]

    # Set aws info
    for ec2 in ['aws', 'ec2']:
        cfg['cloud'][ec2]['username'] = os.environ["AWS_ACCESS_KEY"]
        cfg['cloud'][ec2]['password'] = os.environ["AWS_SECRET_KEY"]

    # Set gce info
    cfg['cloud']['gce']['username'] = os.environ["GCE_USERNAME"]
    cfg['cloud']['gce']['project'] = os.environ["GCE_PROJECT"]
    cfg['cloud']['gce']['ssh_key_data'] = literal(open(os.environ["GCE_KEY_DATA"], 'r').read())

    # Set azure info
    cfg['cloud']['azure']['username'] = os.environ["AZURE_USERNAME"]
    cfg['cloud']['azure']['ssh_key_data'] = literal(open(os.environ["AZURE_KEY_DATA"], 'r').read())

    # Set vmware info
    cfg['cloud']['vmware']['username'] = os.environ["VMWARE_USERNAME"]
    cfg['cloud']['vmware']['password'] = os.environ["VMWARE_PASSWORD"]
    cfg['cloud']['vmware']['host'] = os.environ["VMWARE_HOST"]

    # Set legacy openstack info
    cfg['cloud']['openstack']['username'] = os.environ["OPENSTACK_USERNAME"]
    cfg['cloud']['openstack']['password'] = os.environ["OPENSTACK_PASSWORD"]
    cfg['cloud']['openstack']['host'] = os.environ["OPENSTACK_HOST"]
    cfg['cloud']['openstack']['project'] = os.environ["OPENSTACK_PROJECT"]

    # Set openstack_v2 info
    cfg['cloud']['openstack_v2']['username'] = os.environ["OPENSTACK_V2_USERNAME"]
    cfg['cloud']['openstack_v2']['password'] = os.environ["OPENSTACK_V2_PASSWORD"]
    cfg['cloud']['openstack_v2']['host'] = os.environ["OPENSTACK_V2_HOST"]
    cfg['cloud']['openstack_v2']['project'] = os.environ["OPENSTACK_V2_PROJECT"]

    # Set openstack_v3 info
    cfg['cloud']['openstack_v3']['username'] = os.environ["OPENSTACK_V3_USERNAME"]
    cfg['cloud']['openstack_v3']['password'] = os.environ["OPENSTACK_V3_PASSWORD"]
    cfg['cloud']['openstack_v3']['host'] = os.environ["OPENSTACK_V3_HOST"]
    cfg['cloud']['openstack_v3']['project'] = os.environ["OPENSTACK_V3_PROJECT"]
    cfg['cloud']['openstack_v3']['domain'] = os.environ["OPENSTACK_V3_DOMAIN"]

    # Set SCM info
    cfg['scm']['password'] = os.environ.get("SCM_PASSWORD", "")
    cfg['scm']['ssh_key_data'] = literal(open(os.environ["SCM_KEY_DATA"], 'r').read())
    cfg['scm']['encrypted']['ssh_key_data'] = literal(open(os.environ["SCM_KEY_DATA_ENCRYPTED"], 'r').read())
    cfg['scm']['encrypted']['ssh_key_unlock'] = os.environ.get("SCM_KEY_UNLOCK", "")

    # Set SSH info
    cfg['ssh']['password'] = os.environ.get("SSH_PASSWORD", "")
    cfg['ssh']['ssh_key_data'] = literal(open(os.environ["SSH_KEY_DATA"], 'r').read())
    cfg['ssh']['encrypted']['ssh_key_data'] = literal(open(os.environ["SSH_KEY_DATA_ENCRYPTED"], 'r').read())
    cfg['ssh']['encrypted']['ssh_key_unlock'] = os.environ.get("SSH_KEY_UNLOCK", "")
    cfg['ssh']['vault_password'] = os.environ.get("VAULT_PASSWORD", "")
    cfg['ssh']['sudo_username'] = os.environ.get("SUDO_USERNAME", "")
    cfg['ssh']['sudo_password'] = os.environ.get("SUDO_PASSWORD", "")
    cfg['ssh']['su_username'] = os.environ.get("SU_USERNAME", "")
    cfg['ssh']['su_password'] = os.environ.get("SU_PASSWORD", "")
    cfg['ssh']['become_username'] = os.environ.get("BECOME_USERNAME", "")
    cfg['ssh']['become_password'] = os.environ.get("BECOME_PASSWORD", "")

    # Set github info
    cfg['github']['username'] = os.environ.get("GITHUB_USERNAME", "")
    cfg['github']['token'] = os.environ.get("GITHUB_TOKEN", "")
    cfg['github']['completed'] = os.environ.get("GITHUB_COMPLETED", "").split(',')

    yaml.dump(cfg, open(credentials_file, 'w+'))
