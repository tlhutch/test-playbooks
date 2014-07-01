# (C) 2013, James Laska, <jlaska@ansibleworks.com>

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
import datetime
import junit_xml
import logging

logging.getLogger().setLevel(logging.DEBUG)


class TestCase(junit_xml.TestCase):
    classname = 'ansible-playbook'
    pass


class CallbackModule(object):
    """
    logs playbook results, in results.xml
    """

    def __init__(self, *args, **kwargs):
        self.suites = list()
        self.current_test = None

    def add_suite(self, name):
        self.suites.append(junit_xml.TestSuite(name))

    def add_result(self, host, res):
        logging.debug("host: %s, res: %s" % (host, res))
        self.suites[-1].test_cases.append(TestCase(self.current_test,
                                                   classname=host,
                                                   stdout=res.get('stdout', ''),
                                                   stderr=res.get('stderr', '')))
        # Calculate task elapsed_sec
        if 'delta' in res:
            res_start = res['start']
            res_end = res.get('end', res.get('stop', None))
            assert res_end is not None
            startd = datetime.datetime.strptime(res_start, "%Y-%m-%d %H:%M:%S.%f")
            endd = datetime.datetime.strptime(res.get('end', res.get('stop')), "%Y-%m-%d %H:%M:%S.%f")
            self.suites[-1].test_cases[-1].elapsed_sec = (endd - startd).total_seconds()

    def on_any(self, *args, **kwargs):
        logging.debug("on_any(args:%s, kwargs:%s)" % (args, kwargs))
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        logging.debug("FAILED (%s)" % host)
        self.add_result(host, res)
        self.suites[-1].test_cases[-1].add_failure_info('FAILED (%s)' % res['rc'], res['stderr'])

    def runner_on_ok(self, host, res):
        logging.debug("OK (%s)" % host)
        self.add_result(host, res)

    def runner_on_error(self, host, res):
        logging.debug("ERROR (%s)" % host)
        self.add_result(host, res)
        self.suites[-1].test_cases[-1].add_error_info('ERROR (%s)' % res['rc'], res['stderr'])

    def runner_on_skipped(self, host, item=None):
        logging.debug("SKIPPED (%s)" % host)
        self.add_result(host, dict(invocation='skipped'))
        self.suites[-1].test_cases[-1].add_skipped_info('SKIPPED')

    def runner_on_unreachable(self, host, res):
        self.add_result(host, res)
        self.suites[-1].test_cases[-1].add_failed_info('UNREACHABLE (%s)' % res['rc'], res['stderr'])

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        self.add_result(host, res)

    def runner_on_async_failed(self, host, res, jid):
        self.add_result(host, res)
        self.suites[-1].test_cases[-1].add_failed_info('FAILED (%s)' % res['rc'], res['stderr'])

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        self.current_test = 'TASK: [%s]' % name
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, pattern):
        self.add_suite('PLAY [%s]' % pattern)

    def playbook_on_stats(self, stats):
        logging.debug("playbook_on_stats()")
        fp = open('results.xml', 'wb')
        self.suites[0].to_file(fp, self.suites, prettyprint=True)
        fp.close()
