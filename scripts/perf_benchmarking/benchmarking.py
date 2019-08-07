from argparse import ArgumentParser
import logging
import csv
import os

from awxkit import config, utils


log = logging.getLogger()

cwd = os.path.dirname(__file__)

parser = ArgumentParser()
_instance_help = 'Public IP/DNS for Tower instance.'
parser.add_argument('--instance', dest='instance', help=_instance_help)

_results_help = 'Timestamp file for performance information'
parser.add_argument('--results', dest='results', help=_results_help,
                    default=os.path.join(cwd, 'data.yml'))

_cred_help = 'Credential file to be loaded (default: config/credentials.yml).  Use "false" for none.'
parser.add_argument('--credentials', dest='credentials', help=_cred_help,
                    default=os.path.join(cwd, '..', '..', 'config/credentials.yml'))
_proj_help = 'Project file to be loaded (default: config/projects.yml).  Use "false" for none.'
parser.add_argument('--projects', action="store", dest='projects',
                  default=os.path.join(cwd, '..', '..', 'config/projects.yml'), help=_proj_help)
args = parser.parse_args()

results_file = open(args.results, mode='w', encoding='utf-8')
fieldnames = ['operation', 'user', 'endpoint', 'method', 'elapsed']
result_writer = csv.DictWriter(results_file, fieldnames=fieldnames)
result_writer.writeheader()


config.base_url = "https://{0}".format(args.instance)
if utils.to_bool(args.credentials):
    config.credentials = utils.load_credentials(args.credentials)
if utils.to_bool(args.projects):
    config.project_urls = utils.load_projects(args.projects)


def get_all(endpoint):
    results = []
    resource = endpoint.get()
    while True:
        for result in resource.results:
            results.append(result)
        if not resource.next:
            return results
        resource = resource.next.get()


def determine_job_event_count(jobs):
    total = 0
    for job in jobs:
        total += job.related.job_events.get().count
    return total


def determine_execution_node_counts(jobs):
    result = {}
    for job in jobs:
        if job.execution_node not in result:
            result[job.execution_node] = []
        result[job.execution_node].append(job)
    for node in result:
        result[node] = len(result[node])
    return result


def delete_all(endpoint):
    resource = endpoint.get(page_size=200)
    while True:
        for item in resource.results:
            try:
                item.delete()
            except Exception as e:
                log.info('Failed to delete {0.url}: {1}.'.format(item, e))
        if not resource.next:
            return
        resource = resource.get()


def delete_all_created(v2):
    for endpoint in (v2.jobs, v2.job_templates, v2.projects, v2.inventory, v2.hosts,
                     v2.inventory_scripts, v2.credentials, v2.teams, v2.users, v2.organizations):
        delete_all(endpoint)


def no_op(*a, **kw):
    pass


def write_results(*timedeltas, **kw):
    for delta in timedeltas:
        microseconds = str(delta.microseconds)
        padded_microseconds = ''.join(['0' * (6 - len(microseconds)), microseconds])
        result_writer.writerow(dict(operation=kw.get('operation'),
                                    user=kw.get('user'),
                                    endpoint=kw.get('endpoint'),
                                    method=kw.get('method'),
                                    elapsed="{0.seconds}.{1}".format(delta, padded_microseconds)))
        results_file.flush()
