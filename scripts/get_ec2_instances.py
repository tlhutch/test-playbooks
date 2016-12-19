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
    parser.add_option("--uptime", action="store", dest="uptime",
                      default=None, type="int",
                      help="Only show instances with uptime greater than the value provided (default: %default)")
    parser.add_option("--filter", action="append", dest="filters",
                      default=[],
                      help="Instance filters")
    parser.add_option("--include-protected",
                      action="store_true",
                      dest="include_protected",
                      default=False,
                      help="Include instances with termination protection in match results (default: %default)")

    actions = ['stop', 'terminate']
    parser.add_option("--action", action="store", dest="action",
                      default=None, choices=actions,
                      help="Perform the specified operation on matching instances (choices: %s)" % ', '.join(actions))

    # Parse args
    (opts, args) = parser.parse_args()

    # Check for required credentials
    for required in ['id', 'key']:
        if getattr(opts, required) is None:
            parser.error("Missing required parameter: --%s" % required)

    # Convert filter list to dictionary
    filter_dict = dict()
    for term in opts.filters:
        (k, v) = term.split('=', 1)
        if k not in filter_dict:
            filter_dict[k] = list()
        filter_dict[k].append(v)
    opts.filters = filter_dict

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

        reservations = conn.get_all_instances(filters=opts.filters)

        instances = []
        protected = []

        for r in reservations:
            for i in r.instances:
                if i.get_attribute('disableApiTermination')['disableApiTermination']:
                    protected.append(i)
                else:
                    instances.append(i)

        if opts.include_protected:
            instances += protected

        if instances:
            print("== Instances [region:%s] ==" % region.name)
            for i in instances:
                # Using dateutil.parser results in tzoffset problems when comparing times
                # launch_time = dateutil.parser.parse(i.launch_time)
                launch_time = datetime.strptime(i.launch_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                if opts.uptime is None or (utcnow - launch_time) > timedelta(minutes=opts.uptime):
                    print(" * %s %s (%s) %s" % (i.id, i.public_dns_name, i.launch_time,
                                                ', '.join(["%s=%s" % item for item in i.tags.items()])))
                    if opts.action is not None and hasattr(i, opts.action):
                        getattr(i, opts.action)()
                        print(" ... %s" % opts.action)
                        total_action += 1

    # Display summary
    if opts.action and opts.action == 'terminate':
        print("Instances terminated: %s" % total_action)
    if opts.action and opts.action == 'stop':
        print("Instances stopped: %s" % total_action)
