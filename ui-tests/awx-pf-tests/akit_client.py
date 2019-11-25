"""
This file contains an interaction script with awxkit.

parse_args() just sets up arguments you can provide. The main routine
registers with awxkit then lets you run one of two functions, which either
creates/replaces a resource, or lets you run any awxkit v2 expression.

cypress/support/commands.js interacts with this file.
"""

from awxkit import api, config
import optparse
import os
import pprint
import sys


def parse_args():
    # Build parser
    parser = optparse.OptionParser(usage="{0} akit | create_or_replace [options] BASE_URL".format(sys.argv[0],))
    _name_help = 'Name to be used for the resource.'
    _akitcommand_help = 'A string, passed to awxkit as an arbitrary v2 command. \
            For example, "job_templates()" would call v2.job_templates() in awxkit.'
    _resource_help = 'Specify the type of resource \
            (job_templates, organizations, etc.) to be used. \
            Format is the same as awxkit.'
    parser.add_option(
        '--name',
        action="store",
        dest='name',
        help=_name_help)
    parser.add_option(
        '--akitcommand',
        action="store",
        dest='akitcommand',
        help=_akitcommand_help)
    parser.add_option(
        '--resource',
        action="store",
        dest='resource',
        help=_resource_help)
    # Parse args
    (opts, args) = parser.parse_args()
    return (opts, args)


if __name__ == '__main__':
    (opts, args) = parse_args()

    func = args[0] # either 'akit' or 'create_or_replace'
    config.base_url = args[1] # Base URL of API
    config.credentials = {'default': {
        'username': os.environ['CYPRESS_AWX_E2E_USERNAME'],
        'password': os.environ['CYPRESS_AWX_E2E_PASSWORD'],
    }}
    config.project_urls = {'git': 'https://github.com/ansible/test-playbooks.git'}
    root = api.Api()
    config.use_sessions = True
    root.load_session().get()
    v2 = root.available_versions.v2.get()

    if (func == 'create_or_replace'):
        # Swap 'name' with 'username' if creating a user object
        username = None
        if opts.resource == 'users':
            username = opts.name
            opts.name = None
        resource_obj = getattr(v2, opts.resource)
        pprint.pprint(resource_obj.create_or_replace(
            resource=opts.resource,
            name=opts.name,
            username=username
        ))
    elif (func == 'akit'):
        eval(f'pprint.pprint(v2.{opts.akitcommand})')
