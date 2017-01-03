#!/usr/bin/env python

from argparse import ArgumentParser
import sys

import yaml


parser = ArgumentParser()
parser.add_argument('--cloud_provider', dest='cloud_provider', help='Where to host deployed instances')
parser.add_argument('--platform', dest='platform', help='OS type for instance')
parser.add_argument('--ansible_version', dest='ansible_version', help='Version of ansible to be installed on instance')
args = parser.parse_args()


data = yaml.load(open('playbooks/images-{0.cloud_provider}.yml'.format(args), 'r'))
output = []
for item in data['{0.cloud_provider}_images'.format(args)]:
    if args.platform in item['name']:
        output.append(item)
sys.stdout.write(str(output))
