#!/usr/bin/env python

import logging
import optparse
import sys
import os
import random
import fauxfactory

from towerkit import api, config, utils

LOG_FORMAT = '%(asctime)-15s  %(message)s'  # NOQA
logging.basicConfig(level='INFO', format=LOG_FORMAT)
log = logging.getLogger()


def parse_args():
    # Build parser
    parser = optparse.OptionParser(usage="{0} [options] BASE_URL".format(sys.argv[0],))

    cwd = os.path.dirname(__file__)
    _cred_help = 'Credential file to be loaded (default: config/credentials.yml).  Use "false" for none.'
    parser.add_option('--credentials', action="store", dest='credentials',
                      default=os.path.join(cwd, '..', 'config/credentials.yml'),
                      help=_cred_help)
    parser.add_option("--nodes", action="store", dest="num_nodes",
                      default=os.getenv("RAND_WORKFLOW_NUM_NODES", 5),
                      help="Number of nodes in workflow")
    parser.add_option("--depth", action="store", dest="desired_depth",
                      default=os.getenv('RAND_WORKFLOW_TREE_DEPTH', 3),
                      help="Desired tree depth (note: actual depth varies)")

    # Parse args
    (opts, args) = parser.parse_args()
    if not len(args):
        parser.error("BASE_URL required. (e.g. https://my.tower.com)")
    if len(args) > 1:
        parser.error("Received more arguments than expected. (Should only provide BASE_URL)")

    return (opts, args)


if __name__ == '__main__': # noqa C901
    (opts, args) = parse_args()

    config.base_url = args[0]
    config.credentials = utils.load_credentials(opts.credentials)
    v1 = api.ApiV1().load_default_authtoken().get()
    v1.config.get().install_license()

    # List of potential nodes to build on
    # (uses duplicate nodes to increase likelihood of adding nodes after new root nodes)
    nodes = []
    root_nodes = 1     # Initial root node will be created below
    nodes_in_full_binary_tree = 2**(int(opts.desired_depth) + 1) - 1

    # Create job templates
    passing_jt_id = os.getenv('RAND_WORKFLOW_PASSING_JT_ID')
    failing_jt_id = os.getenv('RAND_WORKFLOW_FAILING_JT_ID')
    name_hash = fauxfactory.gen_alphanumeric()

    if not any((passing_jt_id, failing_jt_id)):
        inventory = v1.hosts.create().ds.inventory

    if not passing_jt_id:
        log.info("Creating Passing Job Template (Use RAND_WORKFLOW_PASSING_JT_ID to specify existing JT)")
        passing_jt = v1.job_templates.create(name='Passing JT - {0}'.format(name_hash), inventory=inventory)
        passing_jt.allow_simultaneous = True
        passing_jt_id = passing_jt.id
    if not failing_jt_id:
        log.info("Creating Failing Job Template (Use RAND_WORKFLOW_FAILING_JT_ID to specify existing JT)")
        failing_jt = v1.job_templates.create(name='Failing JT - {0}'.format(name_hash),
                                             inventory=inventory,
                                             playbook='fail_unless.yml')
        failing_jt.allow_simultaneous = True
        failing_jt_id = failing_jt.id

    # Helpers
    def _get_rand_node():
        return nodes[random.randint(0, len(nodes) - 1)]

    def _has_always_node(node):
        return len(node.get_related('always_nodes').results)

    def _has_success_or_failure_nodes(node):
        return len(node.get_related('success_nodes').results) + \
            len(node.get_related('failure_nodes').results)

    def _rand_payload():
        return dict(unified_job_template=passing_jt_id if random.randint(0, 1) else failing_jt_id)

    def add_leaf_node():
        log.info("Add leaf node")
        node = _get_rand_node()
        if _has_always_node(node):
            nodes.append(node.related.always_nodes.post(_rand_payload()))
        else:
            if _has_success_or_failure_nodes(node):
                if random.randint(0, 1):
                    nodes.append(node.related.success_nodes.post(_rand_payload()))
                else:
                    nodes.append(node.related.failure_nodes.post(_rand_payload()))
            else:
                if random.randint(0, 1):
                    nodes.append(node.related.always_nodes.post(_rand_payload()))
                elif random.randint(0, 1):
                    nodes.append(node.related.success_nodes.post(_rand_payload()))
                else:
                    nodes.append(node.related.failure_nodes.post(_rand_payload()))

    def add_root_node(root_nodes):
        log.info("Add root node")
        node = wfjt.related.workflow_nodes.post(_rand_payload())
        for i in range(len(nodes) / root_nodes):
            nodes.append(node)

    # Create WFJT
    log.info("Create workflow job template")
    wfjt = v1.workflow_job_templates.create()

    # Build workflow
    log.info("Add root node")
    nodes = [wfjt.related.workflow_nodes.post(_rand_payload())]
    for i in range(int(opts.num_nodes) - 1):
        if random.random() < 1.0 / nodes_in_full_binary_tree:
            add_root_node(root_nodes)
            root_nodes += 1
        else:
            add_leaf_node()

    log.info("Workflow ready: {0}/#/templates/workflow_job_template/{1}".format(config.base_url, wfjt.id))
