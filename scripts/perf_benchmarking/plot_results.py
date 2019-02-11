#!/usr/bin/env python

from collections import OrderedDict as OD
from argparse import ArgumentParser
from pprint import pprint
import csv

import numpy as np


# TODO: actual plotting!

parser = ArgumentParser()
_data_help = 'Timestamp file for performance information'
parser.add_argument('--data', dest='data', help=_data_help)

_summary_help = 'Summary to be created'
parser.add_argument('--summary', dest='summary', help=_summary_help)
args = parser.parse_args()


data_file = open(args.data, encoding='utf-8')
reader = csv.DictReader(data_file)

summary_file = open(args.summary, mode='wb', encoding='utf-8')
summary_fields = ['phase', 'average', 'median', 'stdev', 'min', 'max', 'query_count']
writer = csv.DictWriter(summary_file, fieldnames=summary_fields)
writer.writeheader()

# # build result structures
results = OD()
for line in reader:
    operation = line['operation']
    if operation not in results:
        results[operation] = dict(elapsed=[],
                                  average=0,
                                  median=0,
                                  stdev=0,
                                  min=0,
                                  max=0,
                                  query_count=0)
    results[operation]['elapsed'].append(line['elapsed'])

for phase in results:
    phase_results = results[phase]
    elapsed = np.array(phase_results['elapsed']).astype(np.float)
    del phase_results['elapsed']

    phase_results['phase'] = phase
    phase_results['average'] = np.average(elapsed)
    phase_results['median'] = np.median(elapsed)
    phase_results['stdev'] = np.std(elapsed)
    phase_results['min'] = min(elapsed)
    phase_results['max'] = max(elapsed)
    phase_results['query_count'] = len(elapsed)
    writer.writerow(phase_results)

pprint(results)
summary_file.close()

#     # plotscatterplot w/ line
#     plot_scatterplot(phase)

#     # plot histogram w/ line
#     plot_histogram(phase)
