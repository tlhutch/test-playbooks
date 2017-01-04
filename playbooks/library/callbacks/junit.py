# (C) 2014, James Laska, <jlaska@ansible.com>

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
import inspect
import logging
import multiprocessing
import xml.etree.ElementTree as ET

# logger = multiprocessing.log_to_stderr()
# logger.setLevel(multiprocessing.SUBDEBUG)


class JUnitFile(object):
    def __init__(self, filename=os.environ.get('JUNIT_CALLBACK_PATH', 'results.xml'), append=False):
        self.filename = filename
        self.plays = list()

        if append:
            # raise NotImplementedError("FIXME load data from existing XML file")
            self.read(filename)

    @property
    def current_play(self):
        return self.plays[-1]

    @property
    def current_host_event(self):
        return self.current_play.test_cases[-1]

    def add_play(self, **event_data):
        self.plays.append(junit_xml.TestSuite(event_data['name']))

    def add_task(self, **event_data):
        pass

    def add_host_failed(self, **event_data):
        event = self.add_host_event(**event_data)
        if event_data.get('ignore_errors', False):
            event.add_skipped_info(message='failed [%s] => %s\n...ignoring' % (event_data['host'], event_data['res']))
        else:
            event.add_failure_info(message='failed [%s] => %s' % (event_data['host'], event_data['res']))

    def add_host_ok(self, **event_data):
        self.add_host_event(**event_data)

    def add_host_skipped(self, **event_data):
        event = self.add_host_event(**event_data)
        event.add_skipped_info(message='skipping: [%s]' % event_data['host'])

    def add_host_error(self, **event_data):
        event = self.add_host_event(**event_data)
        event.add_error_info(message='fatal [%s] => %s' % (event_data['host'], 'FIXME'))

    def add_host_unreachable(self, **event_data):
        self.add_host_error(**event_data)

    def add_host_event(self, **event_data):
        host = event_data.get('host', '')
        task = event_data.get('task', '')
        role = event_data.get('role', '')
        res = event_data.get('res', {})

        if task == '':
            task = "GATHERING FACTS"
        else:
            if role:
                task = "TASK[%s | %s]" % (role, task)
            else:
                task = "TASK[%s]" % task

        stdout = ''
        stderr = ''
        if isinstance(res, dict):
            stdout = res.get('stdout')
            stderr = res.get('stderr')

        if 'item' in res:
            task += '[item=%s]' % res['item']

        test_case = junit_xml.TestCase(task, classname=host, stdout=stdout, stderr=stderr)

        # Calculate task elapsed_sec
        if 'delta' in res:
            res_start = res['start']
            res_end = res.get('end', res.get('stop', None))
            assert res_end is not None
            startd = datetime.datetime.strptime(res_start, "%Y-%m-%d %H:%M:%S.%f")
            endd = datetime.datetime.strptime(res.get('end', res.get('stop')), "%Y-%m-%d %H:%M:%S.%f")
            diff = endd - startd
            # timedelta.total_seconds() does not work on py26
            test_case.elapsed_sec = (diff.microseconds + (diff.seconds + diff.days*24*3600) * 1e6) / 1e6

        self.current_play.test_cases.append(test_case)
        return test_case
        # return self.current_play.test_cases[-1]

    def read(self, filename=None):
        """Read data from existing junit XML file"""
        if not os.path.isfile(filename or self.filename):
            return

        tree = ET.parse(filename or self.filename)
        root = tree.getroot()
        # Import existing test suites
        for suite in root.iter('testsuite'):
            name = suite.attrib['name']
            id = suite.attrib.get('id', None)
            hostname = suite.attrib.get('hostname', None)
            package = suite.attrib.get('package', None)
            properties = suite.attrib.get('properties', None)
            self.plays.append(junit_xml.TestSuite(name, id=id, hostname=hostname, package=package, properties=properties))

            # Import existing test cases
            for case in suite.iter('testcase'):
                name = case.attrib['name']
                classname = case.attrib['classname']
                time = float(case.attrib.get('time', 0))
                stdout = case.find('system-out')
                stderr = case.find('system-err')
                self.current_play.test_cases.append(junit_xml.TestCase(name, classname=classname, elapsed_sec=time, stdout=stdout, stderr=stderr))

                skipped = case.find('skipped')
                if skipped is not None:
                    self.current_host_event.add_skipped_info(message=skipped.attrib['message'])
                failure = case.find('failure')
                if failure is not None:
                    self.current_host_event.add_failure_info(message=failure.attrib['message'])
                error = case.find('error')
                if error is not None:
                    self.current_host_event.add_error_info(message=error.attrib['message'])

    def write(self, filename=None):
        """Write junit XML file"""
        with open(filename or self.filename, 'wb') as fd:
            self.plays[0].to_file(fd, self.plays, encoding='UTF-8', prettyprint=True)


class CallbackModule(object):
    """
    logs playbook results
    """

    # These events should never have an associated play.
    EVENTS_WITHOUT_PLAY = [
        'playbook_on_start',
        'playbook_on_stats',
    ]
    # These events should never have an associated task.
    EVENTS_WITHOUT_TASK = EVENTS_WITHOUT_PLAY + [
        'playbook_on_setup',
        'playbook_on_notify',
        'playbook_on_import_for_host',
        'playbook_on_not_import_for_host',
        'playbook_on_no_hosts_matched',
        'playbook_on_no_hosts_remaining',
    ]

    def __init__(self, *args, **kwargs):
        self.m = multiprocessing.Manager()
        self.l = self.m.list()
        # self.d = self.m.dict()
        # self.q = multiprocessing.Queue()
        self._init_logging()

    def _init_logging(self):
        try:
            self.junit_callback_debug = int(os.getenv('JUNIT_CALLBACK_DEBUG', '0'))
        except ValueError:
            self.junit_callback_debug = 0
        self.logger = logging.getLogger('ansible.plugins.callback.junit')

        if self.junit_callback_debug >= 2:
            self.logger.setLevel(logging.DEBUG)
        elif self.junit_callback_debug >= 1:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)-8s %(process)-8d %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def _log_event(self, event, **event_data):
        self.logger.info("%s %s [pid:%s]" % (inspect.stack()[0][3], event, os.getpid()))
        self.logger.debug(event_data)

        play = getattr(self, 'play', None)
        play_name = getattr(play, 'name', '')
        if play_name and event not in self.EVENTS_WITHOUT_PLAY:
            event_data['play'] = play_name
        task = getattr(self, 'task', None)
        task_name = getattr(task, 'name', '')
        role_name = getattr(task, 'role_name', '')
        if task_name and event not in self.EVENTS_WITHOUT_TASK:
            event_data['task'] = task_name
        if role_name and event not in self.EVENTS_WITHOUT_TASK:
            event_data['role'] = role_name

        # self.logger.debug("self.q.put('%s', ...)" % event)
        self.logger.debug("self.q.put('%s', %s)" % (event, json.dumps(event_data)))
        self.l.append((event, event_data))
        # self.q.put((event, event_data))

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        self._log_event('runner_on_failed', host=host, res=res,
                        ignore_errors=ignore_errors)

    def runner_on_ok(self, host, res):
        self._log_event('runner_on_ok', host=host, res=res)

    def runner_on_error(self, host, msg):
        self._log_event('runner_on_error', host=host, msg=msg)

    def runner_on_skipped(self, host, item=None):
        self._log_event('runner_on_skipped', host=host, item=item)

    def runner_on_unreachable(self, host, res):
        self._log_event('runner_on_unreachable', host=host, res=res)

    def runner_on_no_hosts(self):
        self._log_event('runner_on_no_hosts')

    def runner_on_async_poll(self, host, res, jid, clock):
        self._log_event('runner_on_async_poll', host=host, res=res, jid=jid,
                        clock=clock)

    def runner_on_async_ok(self, host, res, jid):
        self._log_event('runner_on_async_ok', host=host, res=res, jid=jid)

    def runner_on_async_failed(self, host, res, jid):
        self._log_event('runner_on_async_failed', host=host, res=res, jid=jid)

    def runner_on_file_diff(self, host, diff):
        self._log_event('runner_on_file_diff', host=host, diff=diff)

    def playbook_on_start(self):
        self._log_event('playbook_on_start')

    def playbook_on_notify(self, host, handler):
        self._log_event('playbook_on_notify', host=host, handler=handler)

    def playbook_on_no_hosts_matched(self):
        self._log_event('playbook_on_no_hosts_matched')

    def playbook_on_no_hosts_remaining(self):
        self._log_event('playbook_on_no_hosts_remaining')

    def playbook_on_task_start(self, name, is_conditional):
        self._log_event('playbook_on_task_start', name=name,
                        is_conditional=is_conditional)

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        self._log_event('playbook_on_vars_prompt', varname=varname,
                        private=private, prompt=prompt, encrypt=encrypt,
                        confirm=confirm, salt_size=salt_size, salt=salt,
                        default=default)

    def playbook_on_setup(self):
        self._log_event('playbook_on_setup')

    def playbook_on_import_for_host(self, host, imported_file):
        # don't care about recording this one
        self._log_event('playbook_on_import_for_host', host=host,
                        imported_file=imported_file)
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        # don't care about recording this one
        self._log_event('playbook_on_not_import_for_host', host=host,
                        missing_file=missing_file)
        pass

    def playbook_on_play_start(self, name):
        # Only play name is passed via callback, get host pattern from the play.
        pattern = getattr(getattr(self, 'play', None), 'hosts', name)
        self._log_event('playbook_on_play_start', name=name, pattern=pattern)

    def playbook_on_stats(self, stats):
        """Write Junit XML file describing playbook"""
        # Debugging
        d = {}
        for attr in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
            d[attr] = getattr(stats, attr)
        self._log_event('playbook_on_stats', **d)

        # Create JUnit XML from event queue
        junit = JUnitFile(filename=os.environ.get('JUNIT_CALLBACK_PATH', 'results.xml'),
                          append=True)

        # NOTE: multiprocessing.Queue deadlocks :(
        # while not self.q.empty():
        #     (event, event_data) = self.q.get()
        # for i, (event, event_data) in enumerate(self.l):
        for (i, (event, event_data)) in enumerate(self.l):
            self.logger.debug(event)

            # Debugging
            if event == 'playbook_on_play_start':
                self.logger.debug("%s('%s')" % (event, event_data['play']))
            elif event in ['playbook_on_setup', 'playbook_on_task_start']:
                self.logger.debug("  %s('%s')" % (event, event_data.get('task', 'GATHERING FACTS')))
            elif event.startswith('runner_on_'):
                self.logger.debug("    %s('%s')" % (event, event_data.get('task', '')))

            if event == 'playbook_on_play_start':
                junit.add_play(**event_data)
            elif event == 'playbook_on_setup':
                junit.add_task(**event_data)
            elif event == 'playbook_on_task_start':
                junit.add_task(**event_data)
            elif event == 'runner_on_ok':
                junit.add_host_ok(**event_data)
            elif event == 'runner_on_skipped':
                junit.add_host_skipped(**event_data)
            elif event == 'runner_on_failed':
                junit.add_host_failed(**event_data)
            elif event == 'runner_on_error':
                junit.add_host_error(**event_data)
            elif event == 'runner_on_unreachable':
                junit.add_host_unreachable(**event_data)
            elif event in ['playbook_on_stats', 'playbook_on_notify', 'playbook_on_start']:
                pass

        junit.write()
