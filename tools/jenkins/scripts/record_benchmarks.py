#!/usr/bin/env python

import json
import elasticsearch
import optparse

parser = optparse.OptionParser()

parser.add_option('-e', '--es-url',
                  action="store",
                  dest="es_url")
parser.add_option('-i', '--es-index',
                  action="store",
                  dest="es_index")
parser.add_option('-f', '--awx-fork',
                  action="store",
                  dest="awx_fork")
parser.add_option('-b', '--awx-branch',
                  action="store",
                  dest="awx_branch")
parser.add_option('-j', '--json-stats',
                  action="store",
                  dest="stats_file")

options, args = parser.parse_args()

es = elasticsearch.Elasticsearch([options.es_url])

with open(options.stats_file, 'r') as f:
    stats = json.loads(f.read())

for b in stats['benchmarks']:
    b['awx_fork'] = options.awx_fork
    b['awx_branch'] = options.awx_branch
    b['datetime'] = stats['datetime']
    es.index(index=options.es_index, doc_type="pytest_benchmark", body=b)
