#!/usr/bin/env python
# Copyright 2019 Yanis Guenane  <yguenane@redhat.com>
# Author: Yanis Guenane  <yguenane@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This script takes a Junit file and output errors+failed if any, else number
of passed tests.

This script is used to properly set the build description on Jenkins.
"""

import sys


from junitparser import JUnitXml


def parse_parameters():

    if len(sys.argv) != 2:
        sys.exit('output_junit_results.py: /path/to/junit')

    return sys.argv[1]


def parse_inputs(junit_file):
    """Return the content of the file to output result for."""

    return JUnitXml.fromfile(junit_file)


def get_results(content):

    if content.errors or content.failures:
        return '%s failed %s errors' % (content.failures, content.errors)
    return '%s passed' % (content.tests)


if __name__ == "__main__":
    junit_file = parse_parameters()
    content = parse_inputs(junit_file)
    results = get_results(content)
    print('Final Result>> %s' % results)
