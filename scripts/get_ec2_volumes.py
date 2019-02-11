import os
import sys
import boto
import optparse
import dateutil.parser  # NOQA
from datetime import datetime, timedelta


def parse_args():

    # Build parser
    parser = optparse.OptionParser(usage="%s [options]" % (sys.argv[0],))
    parser.add_option("--id", action="store", dest="id",
                      default=os.environ.get('AWS_ACCESS_KEY', None),
                      help="Amazon ec2 key id")
    parser.add_option("--key", action="store", dest="key",
                      default=os.environ.get('AWS_SECRET_KEY', None),
                      help="Amazon ec2 access key")
    parser.add_option("--age", action="store", dest="age",
                      default=None, type="int",
                      help="Only show volumes with age greater than the value provided (default: %default)")
    parser.add_option("--filter", action="append", dest="filters",
                      default=[],
                      help="Volume filters")

    actions = ['get', 'delete']
    parser.add_option("--action", action="store", dest="action",
                      default=actions[0], choices=actions,
                      help="Perform the specified operation on matching instances (choices: %s)" % ', '.join(actions))

    # Parse args
    (opts, args) = parser.parse_args()

    # Check for required credentials
    for required in ['id', 'key']:
        if getattr(opts, required) is None:
            parser.error("Missing required parameter: --%s" % required)

    # Convert filters list to dictionary
    opts.filters = dict([f.split('=', 1) for f in opts.filters])

    return (opts, args)


if __name__ == '__main__':

    # Parse args
    (opts, args) = parse_args()

    # Establish aws connection
    aws = boto.connect_ec2(aws_access_key_id=opts.id, aws_secret_access_key=opts.key)

    # Get current time
    utcnow = datetime.utcnow()

    # List running instances in all regions
    total_action = 0
    for region in aws.get_all_regions():
        conn = boto.ec2.connect_to_region(region.name,
                                          aws_access_key_id=opts.id,
                                          aws_secret_access_key=opts.key)
        if conn is None:
            print("Failed to connect to region:%s, ignoring." % region.name)
            continue

        volumes = conn.get_all_volumes(filters=opts.filters)
        if volumes:
            print("== Volumes [region:%s] ==" % region.name)
            for vol in volumes:
                # Using dateutil.parser results in tzoffset problems when comparing times
                # create_time = dateutil.parser.parse(vol.create_time)
                create_time = datetime.strptime(vol.create_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                if opts.age is None or (utcnow - create_time) > timedelta(minutes=opts.age):
                    print(" * %s %s/%s (%s) %s" % (
                        vol.id, vol.status, vol.attachment_state(),
                        vol.create_time,
                        ', '.join(["%s=%s" % item for item in vol.tags.items()])
                    ))

                if opts.action is not None and hasattr(vol, opts.action):
                    getattr(vol, opts.action)()
                    print(" ... %s" % opts.action)
                    total_action += 1

    # Display summary
    if opts.action and opts.action == 'delete':
        print("Volumes deleted: %s" % total_action)
