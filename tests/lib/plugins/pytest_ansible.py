import os
import py
import pipes
import subprocess
import requests
import ansible.runner
import ansible.inventory
from urlparse import urlparse

__version__ = '1.0'

def pytest_sessionstart(session):
    '''
    Sanitize --ansible-* parameters.
    Ensure --ansible-inventory references a valid file. If a remote URL is
    used, download the file locally.
    '''

    # Yuck, is there a better way to benefit from pytest_tmpdir?
    tmpdir = session.config.pluginmanager.getplugin("tmpdir").TempdirHandler(\
        session.config).getbasetemp()

    # Sanitize ansible_hostname
    ansible_hostname = session.config.getvalue('ansible_host_pattern')
    # If using pytest_mozwebqa, just use the the value of --baseurl
    if ansible_hostname is None and hasattr(session.config.option, 'base_url'):
        # attempt to use --baseurl as ansible_host_pattern
        ansible_hostname = urlparse(session.config.getvalue('base_url')).hostname
    if ansible_hostname is None:
        py.test.exit("No ansible host pattern provided (--ansible-host-pattern)")

    # Sanitize ansible_inventory
    ansible_inventory = session.config.getvalue('ansible_inventory')
    if not session.config.option.collectonly:
        # Download remote inventory file locally first
        if '://' in ansible_inventory:
            try:
                r = requests.get(ansible_inventory)
            except Exception, e:
                py.test.exit("Unable to download ansible inventory file - %s" % e)

            local_inventory = tmpdir.mkdir("ansible").join("inventory.ini").open('a+')
            for line in r.text.split('\n'):
                # Detect if a host alias is used.  A host alias won't match
                # with base_url.
                if ansible_hostname in line and not line.startswith(ansible_hostname):
                    line = "%s %s" % (ansible_hostname, line.split(' ',1).pop())
                local_inventory.write(line + '\n')

            # Remember the local filename
            ansible_inventory = local_inventory.name
            session.config.option.ansible_inventory = local_inventory.name

        # Verify the inventory file exists
        if not os.path.exists(ansible_inventory):
            py.test.exit("Ansible inventory file not found: %s" % ansible_inventory)


def pytest_funcarg__ansible_runner(request):
    '''
    Return initialized ansibleWrapper
    '''
    inventory = request.config.getvalue('ansible_inventory')
    hostname = urlparse(request.config.getvalue('base_url')).hostname
    return AnsibleWrapper(inventory, hostname)


def pytest_addoption(parser):
    group = parser.getgroup('ansible', 'ansible')
    group._addoption('--ansible-inventory',
                     action='store',
                     dest='ansible_inventory',
                     default='/etc/ansible/hosts',
                     metavar='ANSIBLE-INVENTORY',
                     help='Location of ansible inventory file')

    group._addoption('--ansible-host-pattern',
                     action='store',
                     dest='ansible_host_pattern',
                     default=None,
                     metavar='ANSIBLE-HOST-PATTERN',
                     help='Specify ansible host pattern')


class AnsibleWrapper(object):
    '''
    Wrapper around ansible.runner.Runner()

    == Examples ==
    aw = AnsibleWrapper('/path/to/inventory')
    results = aw.command('mkdir /var/lib/testing', creates='/var/lib/testing')

    results = aw.git(repo='https://github.com/ansible/ansible.git', dest='/tmp/ansible')
    '''

    def __init__(self, inventory, pattern='all'):
        self.inventory = inventory
        self.pattern = pattern
        self.module_name = None

    def __getattr__(self, name):
        self.module_name = name
        #return self.ansible_runner
        return self.subprocess_runner

    def ansible_runner(self, *args, **kwargs):
        # Assemble module argument string
        module_args = [pipes.quote(s) for s in args]
        if kwargs:
            module_args += ["%s=%s" % i for i in kwargs.items()]
        module_args = ' '.join(module_args)

        inventory = ansible.inventory.Inventory(self.inventory)

        runner = ansible.runner.Runner(
           inventory=inventory,
           pattern=self.pattern,
           module_name=self.module_name,
           module_args=module_args,
           )
        return runner.run()

    def subprocess_runner(self, *args, **kwargs):

        # Build module arguments
        module_args = []
        if args:
            module_args += list(args)
        if kwargs:
            module_args += ["%s=%s" % i for i in kwargs.items()]

        # Build command
        cmd = ['ansible', self.pattern, '-m', self.module_name, '-i', self.inventory, '--sudo']
        if module_args:
            cmd += ['-a', ' '.join(module_args)]

        popen = subprocess.Popen(cmd, shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        stdout = popen.communicate()[0]
        if popen.returncode:
            raise Exception("Command failed (%s): %s\n%s" % (popen.returncode, cmd, stdout))
        return stdout
