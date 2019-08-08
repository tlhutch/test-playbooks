import json
import os
import subprocess
import yaml

import pytest

from awxkit import config


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
def cli():
    def run(args, *a, **kw):
        if 'stdout' not in kw:
            kw['stdout'] = subprocess.PIPE
        if 'stderr' not in kw:
            kw['stderr'] = subprocess.STDOUT
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
        return CompletedProcessProxy(subprocess.run(args, *a, **kw))
    return run
