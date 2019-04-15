#!/usr/bin/env python

from argparse import ArgumentParser
import sys

import yaml


parser = ArgumentParser()
parser.add_argument('--cloud_provider', dest='cloud_provider', help='Where to host deployed instances')
parser.add_argument('--platform', dest='platform', help='OS type for instance')
parser.add_argument('--ansible_version', dest='ansible_version', default=None, help='Version of ansible to be installed on instance')
parser.add_argument('--groups', dest='desired_groups', default=None, help='Inventory groups for image matches (overrides images-cloud_provider var)')
args = parser.parse_args()

data = yaml.safe_load(open('playbooks/images-{0.cloud_provider}.yml'.format(args), 'r'))
output = []
for item in data['{0.cloud_provider}_images'.format(args)]:
    if args.platform in item['name']:
        if args.desired_groups is not None:
            item['groups'] = args.desired_groups
        output.append(item)
sys.stdout.write(str(output))
