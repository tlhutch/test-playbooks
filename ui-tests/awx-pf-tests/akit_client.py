"""
This file contains an interaction script with awxkit.

parse_args() just sets up arguments you can provide. The main routine
registers with awxkit then lets you run one of two functions, which either
creates/replaces a resource, or lets you run any awxkit v2 expression.

cypress/support/commands.js interacts with this file.
"""

from awxkit import api, config, utils
import optparse
import os
import sys


def parse_args():
    # Build parser
    parser = optparse.OptionParser(usage="{0} akit | create_or_replace [options] BASE_URL".format(sys.argv[0],))
    cwd = os.path.dirname(__file__)
    _cred_help = 'Credential file to be loaded (default: config/credentials.yml). \
            Use "false" for none.'
    _proj_help = 'Project file to be loaded (default: config/projects.yml). \
            Use "false" for none.'
    _name_help = 'Name to be used for the resource.'
    _akitcommand_help = 'A string, passed to awxkit as an arbitrary v2 command. \
            For example, "job_templates()" would call v2.job_templates() in awxkit.'
    _resource_help = 'Specify the type of resource \
            (job_templates, organizations, etc.) to be used. \
            Format is the same as awxkit.'
    parser.add_option(
        '--credentials',
        action="store",
        dest='credentials',
        default=os.path.join(cwd, '..', '..', 'config/credentials.yml'),
        help=_cred_help)
    parser.add_option(
        '--projects',
        action="store",
        dest='projects',
        default=os.path.join(cwd, '..', '..', 'config/projects.yml'),
        help=_proj_help)
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
    config.credentials = utils.load_credentials(opts.credentials)
    config.project_urls = utils.load_projects(opts.projects)

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
        if opts.resource == 'job_templates' or opts.resource == 'projects':
            jt_object = resource_obj.create_or_replace(
                resource=opts.resource,
                name=opts.name,
                username=username
            )
            # import pdb; pdb.set_trace()
            jt_object_json = '{ "name": "'+ str(jt_object.name) +'", "id": '+ str(jt_object.id) + '}'
            print(jt_object_json)
        else:
            print(resource_obj.create_or_replace(
                resource=opts.resource,
                name=opts.name,
                username=username
            ))
    elif (func == 'akit'):
        eval(f'print(v2.{opts.akitcommand})')
