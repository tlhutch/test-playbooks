#!/usr/bin/env python

import sys
import os
import yaml

if len(sys.argv) != 3:
    echo "usage: %s <template> <output_file>" % sys.argv[0]

# FIXME - support optparser parameters
(credentials_template, credentials_file) = sys.argv[1:3]

# Gather SCM private key credentials
if not "SCM_KEY_DATA" in os.environ:
    os.environ["SCM_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/id_rsa.github-ansible-jenkins-nopassphrase")
if not "SCM_KEY_DATA_ENCRYPTED" in os.environ:
    os.environ["SCM_KEY_DATA_ENCRYPTED"] = os.path.expandvars("$HOME/.ssh/id_rsa.github-ansible-jenkins-passphrase")

# Gather SSH private key credentials
if not "SSH_KEY_DATA" in os.environ:
    os.environ["SSH_KEY_DATA"] = os.path.expandvars("$HOME/.ssh/id_rsa.jenkins-nopassphrase")
if not "SSH_KEY_DATA_ENCRYPTED" in os.environ:
    os.environ["SSH_KEY_DATA_ENCRYPTED"] = os.path.expandvars("$HOME/.ssh/id_rsa.jenkins-passphrase")

# Allow for folded/literal yaml blocks (see
# http://stackoverflow.com/questions/6432605/any-yaml-libraries-in-python-that-support-dumping-of-long-strings-as-block-liter)
class folded(unicode): pass
def folded_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')
yaml.add_representer(folded, folded_representer)

class literal(unicode): pass
def literal_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
yaml.add_representer(literal, literal_representer)

# Import credentials.template
cfg = yaml.load(open(credentials_template, 'r'))

# Set default admin password
cfg['default']['password'] = os.environ["AWX_ADMIN_PASSWORD"]

# Set rackspace info
for rax in ['rackspace','rax']:
    cfg['cloud'][rax]['username'] = os.environ["RAX_USERNAME"]
    cfg['cloud'][rax]['password'] = os.environ["RAX_API_KEY"]

# Set aws info
for ec2 in ['aws','ec2']:
    cfg['cloud'][ec2]['username'] = os.environ["AWS_ACCESS_KEY"]
    cfg['cloud'][ec2]['password'] = os.environ["AWS_SECRET_KEY"]

# Set SCM info
cfg['scm']['password'] = os.environ["SCM_PASSWORD"]
cfg['scm']['ssh_key_data'] = literal(open(os.environ["SCM_KEY_DATA"],'r').read())
cfg['scm']['encrypted']['ssh_key_data'] = literal(open(os.environ["SCM_KEY_DATA_ENCRYPTED"],'r').read())
cfg['scm']['encrypted']['ssh_key_unlock'] = os.environ["SCM_KEY_UNLOCK"]

# Set SSH info
cfg['ssh']['password'] = os.environ["SSH_PASSWORD"]
cfg['ssh']['ssh_key_data'] = literal(open(os.environ["SSH_KEY_DATA"],'r').read())
cfg['ssh']['encrypted']['ssh_key_data'] = literal(open(os.environ["SSH_KEY_DATA_ENCRYPTED"],'r').read())
cfg['ssh']['encrypted']['ssh_key_unlock'] = os.environ["SSH_KEY_UNLOCK"]

yaml.dump(cfg, open(credentials_file, 'w+'))
