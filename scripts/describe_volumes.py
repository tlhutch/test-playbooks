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
                        help="Only show volumes in the provided region (default: all)")
    parser.add_argument("--key", action="store", dest="key",
                        default=os.environ.get('AWS_SECRET_KEY', None),
                        help="Amazon ec2 access key")
    parser.add_argument("--uptime", action="store", dest="uptime",
                        default=None, type=int,
                        help="Only show volumes with uptime greater than the provided hours (default: %(default)s)")
    parser.add_argument("--filter", action="append", dest="filters",
                        default=[],
                        help="Volume filters")
    parser.add_argument("--exclude", action="append", dest="excludes",
                        default=[],
                        help="Exclude volume matching the provided JMESPath query "
                        "(http://jmespath.org/tutorial.html)")
    parser.add_argument("--delete", action="store_true", dest="delete",
                        default=False,
                        help="Delete matching volumes.")

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


def is_excluded(ec2, excludes=[]):
    '''Return whether the provided volume matches the exclude filters.'''

    def _(volume):
        # Test if volume should be excluded
        for exclude in excludes:
            if jmespath.search(exclude, volume):
                return False
        return True
    return _


def display_volume(region, volume):
    # calculate age in hours
    age = int((datetime.utcnow() - volume['CreateTime']).total_seconds() / 60 / 60)

    # {u'AvailabilityZone': 'eu-west-1b', u'Attachments': [{u'AttachTime': datetime.datetime(2016, 5, 29, 1, 34, 16,
    # tzinfo=tzutc()), u'InstanceId': 'i-5bfbb1d1', u'VolumeId': 'vol-31c1e9c3', u'State': 'attached',
    # u'DeleteOnTermination': True, u'Device': '/dev/sda1'}], u'Encrypted': False, u'VolumeType': 'gp2', u'VolumeId':
    # 'vol-31c1e9c3', u'State': 'in-use', u'Iops': 100, u'SnapshotId': 'snap-02012b28', u'CreateTime':
    # datetime.datetime(2016, 5, 29, 1, 34, 16, 623000), u'Size': 8}

    print(
        "{VolumeId} RegionName:{0} State:{State} Size:{Size} Uptime{1} {2}".format(
            region, age,
            ", ".join(["{InstanceId}:{State}".format(**attach) for attach in volume.get('Attachments', [])]),
            **volume
        )
    )


if __name__ == '__main__':

    # Parse args
    args = parse_args()

    # Establish aws connection
    session = boto3.session.Session(aws_access_key_id=args.id, aws_secret_access_key=args.key)

    # Determine oldest launch_time
    if args.uptime is None:
        oldest_create_time = datetime.utcnow() + timedelta(days=30 * 365)
    else:
        oldest_create_time = datetime.utcnow() - timedelta(hours=args.uptime)

    # Sanitize --region parameter
    all_regions = session.get_available_regions('ec2')
    for region in args.regions:
        if region not in all_regions:
            sys.exit('No such region `{0}`'.format(region))
    if not args.regions:
        args.regions = all_regions

    # List running volumes in all regions
    count = 0
    for region in args.regions:
        ec2 = boto3.client('ec2', region_name=region, aws_access_key_id=args.id, aws_secret_access_key=args.key)
        if ec2 is None:
            print("Failed to connect to region:%s, ignoring." % region)
            continue

        # Query matching volumes
        paginator = ec2.get_paginator('describe_volumes')
        page_iterator = paginator.paginate(Filters=process_filters(args.filters))

        # Track volume ids for possible termination or stop
        matching_volume_ids = []

        for page in page_iterator:

            # Filter based on termination protection
            # page['Volumes'] = filter(is_protected(ec2, args.protected), page['Volumes'])
            # page['Volumes'] = filter(is_excluded(ec2, args.excludes), page['Volumes'])

            for volume in page['Volumes']:

                # Assert both datetimes are offset aware
                volume['CreateTime'] = volume['CreateTime'].replace(tzinfo=oldest_create_time.tzinfo)
                if volume['CreateTime'] < oldest_create_time:
                    display_volume(region, volume)
                    count += 1

                    # Optionally Delete Volume
                    if args.delete:
                        ec2.delete_volume(VolumeId=volume['VolumeId'])
    if count:
        action_performed = args.delete and 'deleted' or ''
        print("Total volumes: {0} {1}".format(count, action_performed))
