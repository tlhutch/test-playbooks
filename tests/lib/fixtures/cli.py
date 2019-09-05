import json
import os
import subprocess
import yaml

import pytest

from awxkit import config
from awxkit import api


class CompletedProcessProxy(object):

    def __init__(self, result):
        self.result = result

    def __getattr__(self, attr):
        return getattr(self.result, attr)

    @property
    def json(self):
        return json.loads(self.stdout)

    @property
    def yaml(self):
        return yaml.safe_load(self.stdout)


@pytest.fixture(scope='function')
def cli(connection, request):
    def run(args, *a, **kw):
        kw['encoding'] = 'utf-8'
        if 'stdout' not in kw:
            kw['stdout'] = subprocess.PIPE
        if 'stderr' not in kw:
            kw['stderr'] = subprocess.STDOUT
        if 'teardown' in kw:
            teardown = kw.pop('teardown')
        else:
            teardown = False
        if kw.pop('auth', None) is True:
            args = [
                'awx',
                '-k', # SSL verify false
                '--conf.color', 'f'
            ] + args[1:]
            kw.setdefault('env', {}).update({
                'PATH': os.environ['PATH'],
                'TOWER_HOST': config.base_url,
                'TOWER_USERNAME': config.credentials.users.admin.username,
                'TOWER_PASSWORD': config.credentials.users.admin.password,
            })

        ret = CompletedProcessProxy(subprocess.run(args, *a, **kw))

        if teardown:
            if not hasattr(ret, 'json'):
                raise AttributeError('No JSON in response, cannot teardown! Is this a deletable object?')

            if 'url' not in ret.json:
                raise AttributeError('Unable to get the created object as it has no "url" attribute. We cannot perform teardown')

            page = api.page.TentativePage(ret.json['url'], connection).get()
            request.addfinalizer(page.silent_delete)

        return ret
    return run
