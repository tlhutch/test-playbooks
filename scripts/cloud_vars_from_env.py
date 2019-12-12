#!/usr/bin/env python
from argparse import ArgumentParser
import yaml
import sys
import os
import random
import time
import string

# Purpose: To generate cloud instance vars for the deploy playbooks of the form:
# ec2_images: [{'name': 'rhel-7.4-x86_64', 'user': 'ec2-user', 'id': 'ami-c998b6b2',
#               'type': 'm3.medium', 'groups': 'tower,instance_group_non_default',
#               'security_group': 'Tower'}]
# gce_images: [{'name': 'centos-6',  'image': 'centos-6',
#               'machine_type': 'n1-standard-1', 'zone': 'us-central1-a'}]

# This is done by sourcing the following environment variables:
# CLOUD_PROVIDER, PLATFORM and
env_vars = ['AUTHORIZED_KEYS', 'DELETE_ON_START', 'MINIMUM_VAR_SPACE', 'OUT_OF_BOX_OS', 'TOWER_VERSION']
# as well as environment variables with the prefixes:
prefixes = ['ANSIBLE', 'AW_', 'AWS', 'AWX', 'AZURE', 'CREATE_EC2', 'EC2',
            'GALAXY', 'GCE', 'INSTANCE', 'TERMINATE_EC2']
# and obtaining the desired image vars from playbooks/images-{cloud-provider}.yml.
# If any of the following environment variables aren't provided and the cloud image
# variable files are missing them, a random 10 character value will be generated:
passwords = ['AWX_ADMIN_PASSWORD', 'AWX_PG_PASSWORD', 'AWX_RABBITMQ_PASSWORD']


def parse_args():
    provider_types = ('azure', 'ec2', 'gce', 'all')
    parser = ArgumentParser()
    parser.add_argument('--image-vars', dest='image_vars', default=None,
                        help='Cloud image variable yaml file')
    parser.add_argument('--cloud-provider', dest='cloud_provider',
                        default=os.environ.get('CLOUD_PROVIDER'),
                        help='Where to host deployed instances. Can be one of {}.'
                             .format(provider_types))
    parser.add_argument('--platform', dest='platform',
                        default=os.environ.get('PLATFORM'),
                        help='OS type for instance.  If "all" no {cloud-provider}_images '
                             'variable will be set in the output.')
    parser.add_argument('--ansible-version', dest='ansible_version', default=None,
                        help='Version of ansible to be installed on instance')
    parser.add_argument('--groups', dest='desired_groups', default=None,
                        help='Inventory groups for image matches '
                             '(overrides images-cloud-provider var)')
    parser.add_argument('--eip', dest='eip', action='store_true',
                        help='ec2 should be associated w/ eip')

    args = parser.parse_args()
    if not args.cloud_provider:
        raise TypeError('--cloud-provider (or CLOUD_PROVIDER env var) is required.')
    if not args.platform:
        raise TypeError('--platform (or PLATFORM env var) is required.')
    if args.cloud_provider not in provider_types:
        raise TypeError('--cloud-provider must be one of {}'.format(provider_types))
    return args


def random_password(length=16):
    if (int(time.time()) % 2) == 0:
        password = ''.join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=length))
    else:
        # Single and double quote are not properly handled currently. Hence
        # removing them from the set of usable chracter
        sub_printable = string.printable.replace("'", "").replace('"', '')
        # Remove / and \ since they get weird results with bash and all nested
        # escaping levels when running the pipelines
        sub_printable = sub_printable.replace('/', '').replace('\\', '').strip()
        # Remove ` as it seems to be creating issues when deploying - to be re-enabled
        # when root cause is found
        sub_printable = sub_printable.replace('`', '').strip()
        # Remove { and } as it creates issue with jinja templating
        sub_printable = sub_printable.replace('{', '').replace('}', '').strip()

        # Make sure we always start with an ascii letter as it is a common
        # requirements for passwords.
        password = 'a' + ''.join(random.SystemRandom().choices(sub_printable, k=length))

    return password


def prune_image_vars(image_vars):
    for variable in ('_ec2_elastic_ips', 'user_data_install_py2'):
        image_vars.pop(variable, None)
    return image_vars


def cloud_image_vars(image_vars, args):
    """Mutates image_vars (from yml files) to match desired filter and value updates"""
    if args.cloud_provider == 'all' and args.platform == 'all':
        return image_vars

    cloud_image_vars = dict(azure_images=[], ec2_images=[], gce_images=[])

    provider_images_key = '{0.cloud_provider}_images'.format(args)
    if args.platform == 'all':
        image_vars.pop(provider_images_key, None)
        del cloud_image_vars[provider_images_key]
        image_vars.update(cloud_image_vars)
        return prune_image_vars(image_vars)

    if args.cloud_provider == 'all':
        providers = ('azure_images', 'ec2_images', 'gce_images')
    else:
        providers = (provider_images_key,)

    for provider in providers:
        for item in image_vars.get(provider, {}):
            if args.platform in item['name']:
                if args.desired_groups is not None:
                    item['groups'] = args.desired_groups
                if provider == 'ec2_images' and args.eip:
                    for eip in image_vars.get('_ec2_elastic_ips', {}):
                        if eip['name'] in item['name']:
                            item['eip'] = eip['eip']
                cloud_image_vars[provider].append(item)

    image_vars.update(cloud_image_vars)
    return prune_image_vars(image_vars)


def password_vars(image_vars):
    env = os.environ
    password_vars = {}
    for password_env_var in passwords:
        password_key = password_env_var.lower().split('awx_')[1]
        if password_env_var in env:
            password_vars[password_key] = env[password_env_var]
        elif password_key not in image_vars:
            password_vars[password_key] = random_password()
    return password_vars


def variables_from_env_vars():
    env = os.environ
    env_var_vars = {}
    for env_var in env_vars:
        if env_var in env:
            if env_var == 'AUTHORIZED_KEYS':
                var_value = env[env_var].split(',')
            else:
                var_value = env[env_var]
            env_var_vars[env_var.lower()] = var_value
    for env_var in env:
        for prefix in prefixes:
            if env_var.startswith(prefix):
                env_var_vars[env_var.lower()] = env[env_var]

    return env_var_vars


def main():
    args = parse_args()
    image_path = ''
    if args.image_vars is not None:
        image_path = args.image_vars
    elif args.cloud_provider != 'all':
        tqa_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
        image_path = os.path.join(tqa_root, 'playbooks/images-{0.cloud_provider}.yml'
                                            .format(args))

    image_vars = yaml.safe_load(open(image_path, encoding='utf-8')) if image_path else {}
    image_vars = cloud_image_vars(image_vars, args)
    image_vars.update(password_vars(image_vars))
    image_vars.update(variables_from_env_vars())
    sys.stdout.write(yaml.dump(image_vars))


if __name__ == '__main__':
    main()
