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
This script takes two junit files, and override the results from the test ids
found in the second one onto the other one.

The current pattern to run pytest is to run pytest, sleep and then rerun
pytest --lf. Each pytest call generates its own junit output file. Goal of
this script is to update first output with status of second output
"""

import sys


from junitparser import JUnitXml


def parse_parameters():

    if len(sys.argv) != 4:
        sys.exit('override_junit.py: original-junit to-override-junit new-junit')

    return sys.argv[1], sys.argv[2], sys.argv[3]


def parse_inputs(original_file, to_override_file):
    """Return the content of the two files."""

    original_content = JUnitXml.fromfile(original_file)
    content_to_override = JUnitXml.fromfile(to_override_file)

    return original_content, content_to_override


def write_new_file(suite, new_file):
    """Write new JUnit output."""

    xml = JUnitXml()
    xml.add_testsuite(suite)
    xml.write(new_file)


def override_content(original_content, content_to_override):

    cases_to_override = {}
    original_cases = {}

    for case in content_to_override:
        if (hasattr(case.result, '_tag') and not case.result._tag == 'failure') or \
                not hasattr(case.result, '_tag'):
            cases_to_override[case.name] = case

    for case in original_content:
        if case.name in cases_to_override.keys():
            original_cases[case.name] = case

    for case in cases_to_override.keys():
        original_content.remove_testcase(original_cases[case])
        original_content.add_testcase(cases_to_override[case])

    return original_content


if __name__ == "__main__":
    original_file, to_override_file, new_file = parse_parameters()
    original_content, content_to_override = parse_inputs(original_file, to_override_file)
    new_content = override_content(original_content, content_to_override)
    write_new_file(new_content, new_file)
