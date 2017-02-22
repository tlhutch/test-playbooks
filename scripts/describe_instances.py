#!/usr/bin/env python

import os
import sys
import boto3
import argparse
import jmespath
import dateutil.parser  # NOQA
from datetime import datetime, timedelta


def parse_args():

    # Build parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", action="store", dest="id",
                        default=os.environ.get('AWS_ACCESS_KEY', None),
                        help="Amazon ec2 key id")
    parser.add_argument("--region", action="append", dest="regions",
                        default=[],
                        help="Only show instances in the provided region (default: all)")
    parser.add_argument("--key", action="store", dest="key",
                        default=os.environ.get('AWS_SECRET_KEY', None),
                        help="Amazon ec2 access key")
    parser.add_argument("--uptime", action="store", dest="uptime",
                        default=None, type=int,
                        help="Only show instances with uptime greater than the provided hours (default: %(default)s)")
    parser.add_argument("--filter", action="append", dest="filters",
                        default=[],
                        help="Instance filters")
    parser.add_argument("--exclude", action="append", dest="excludes",
                        default=[],
                        help="Exclude instances matching the provided JMESPath query "
                        "(http://jmespath.org/tutorial.html)")
    parser.add_argument("--protected",
                        action="store_true",
                        dest="protected",
                        default=False,
                        help="Include instances with termination protection in match results (default: %(default)s)")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--stop", action="store_true", dest="stop",
                       default=False,
                       help="Stop matching instances.")
    group.add_argument("--terminate", action="store_true", dest="terminate",
                       default=False,
                       help="Terminate matching instances.")

    # Parse args
    args = parser.parse_args()

    # Check for required credentials
    for required in ['id', 'key']:
        if getattr(args, required) is None:
            parser.error("Missing required parameter: --%s" % required)

    return args


def process_filters(filters):
    # Convert filter list to dictionary
    filter_dict = dict()
    for term in filters:
        (k, v) = term.split('=', 1)
        if k not in filter_dict:
            filter_dict[k] = list()
        filter_dict[k].append(v)

    # Now convert back to a list for boto3
    filter_list = list()
    for k, v in filter_dict.items():
        filter_list.append(dict(Name=k, Values=v))

    return filter_list


def is_protected(ec2, include_protected=False):
    """Return whether the provided instance has termination protection enabled."""
    def _(instance):
        if include_protected:
            return True
        else:
            return not ec2.describe_instance_attribute(InstanceId=instance['InstanceId'], Attribute='disableApiTermination')['DisableApiTermination']['Value']

    return _


def is_excluded(ec2, excludes=[]):
    """Return whether the provided instance matches the exclude filters."""
    def _(instance):
        # Test if instance should be excluded
        for exclude in excludes:
            if jmespath.search(exclude, instance):
                return False
        return True
    return _


def display_instance(region, instance):
    # calculate age in hours
    age = int((datetime.utcnow() - instance['LaunchTime']).total_seconds() / 60 / 60)

    # hack to inject KeyName as a tag.  This makes displaying the key easier below.
    if 'KeyName' in instance:
        if 'Tags' not in instance:
            instance['Tags'] = []
        instance['Tags'].append(dict(Key='KeyName', Value=instance['KeyName']))

    # display instance info
    print(
        "{InstanceId} {PublicDnsName} RegionName:{0} State:{State[Name]} Uptime:{1}h {2}".format(
            region, age,
            ", ".join(["{Key}:{Value}".format(**tag) for tag in instance.get('Tags', [])]), **instance)
    )


if __name__ == '__main__':

    # Parse args
    args = parse_args()

    # Establish aws connection
    session = boto3.session.Session(aws_access_key_id=args.id, aws_secret_access_key=args.key)

    # Determine oldest launch_time
    if args.uptime is None:
        oldest_launch_time = datetime.utcnow() + timedelta(days=30 * 365)
    else:
        oldest_launch_time = datetime.utcnow() - timedelta(hours=args.uptime)

    # Sanitize --region parameter
    all_regions = session.get_available_regions('ec2')
    for region in args.regions:
        if region not in all_regions:
            sys.exit('No such region `{0}`'.format(region))
    if not args.regions:
        args.regions = all_regions

    # List running instances in all regions
    count = 0
    for region in args.regions:
        ec2 = boto3.client('ec2', region_name=region, aws_access_key_id=args.id, aws_secret_access_key=args.key)
        if ec2 is None:
            print("Failed to connect to region:%s, ignoring." % region)
            continue

        # Query matching instances
        # reservations = ec2.describe_instances(Filters=process_filters(args.filters))
        paginator = ec2.get_paginator('describe_instances')
        page_iterator = paginator.paginate(Filters=process_filters(args.filters))

        # The following doesn't work
        # filter_iterator = page_iterator.search("Reservations[].Instances[?LaunchTime<`{0}`]".format(oldest_launch_time))
        # for reservations in filter_iterator:

        # Track instance ids for possible termination or stop
        matching_instance_ids = []

        for reservations in page_iterator:

            for reservation in reservations['Reservations']:
                # Filter based on termination protection
                reservation['Instances'] = filter(is_protected(ec2, args.protected), reservation['Instances'])

                # Filter based on exclusions
                reservation['Instances'] = filter(is_excluded(ec2, args.excludes), reservation['Instances'])

                for instance in reservation['Instances']:
                    # Assert both datetimes are offset aware
                    instance['LaunchTime'] = instance['LaunchTime'].replace(tzinfo=oldest_launch_time.tzinfo)
                    if instance['LaunchTime'] < oldest_launch_time:
                        display_instance(region, instance)
                        matching_instance_ids.append(instance['InstanceId'])
                        count += 1

                # Perform action (stop/terminate)
                if matching_instance_ids and any([args.stop, args.terminate]):
                    func = getattr(ec2, args.stop and 'stop_instances' or 'terminate_instances')
                    func(InstanceIds=matching_instance_ids)
    if count:
        action_performed = args.stop and 'stopped' or args.terminate and 'terminated' or ''
        print("Total instances: {0} {1}".format(count, action_performed))
