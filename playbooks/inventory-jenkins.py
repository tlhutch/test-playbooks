#!/usr/bin/env python

import os
import sys
import json
import requests
import http.client
import argparse
import tempfile
import configparser
import ansible
import ansible.inventory
from pkg_resources import parse_version
from urllib.parse import urljoin

has_ansible_v2 = parse_version(ansible.__version__) >= parse_version('2.0.0')
if has_ansible_v2:
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.utils.vars import load_extra_vars

job_path = '/job/Test_Tower_Install/ANSIBLE_NIGHTLY_BRANCH={ansible_nightly_branch},PLATFORM={platform},label={label}/lastBuild'
artifact_path = '/artifact/playbooks/inventory.log/*view*/'
ansible_nightly_branches = ['devel', 'stable-2.2', 'stable-2.1']
supported_platforms = ['rhel-7.2-x86_64', 'centos-7.latest-x86_64', 'ol-7.2-x86_64',
                       'ubuntu-14.04-x86_64', 'ubuntu-16.04-x86_64', ]


class AnsibleInventory(configparser.ConfigParser):

    def write_ini(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % self.DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s=%s\n" % (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section.strip())
            for (key, value) in self._sections[section].items():
                if key == "__name__":
                    continue
                if (value is not None) or (self._optcre == self.OPTCRE):
                    key = "=".join((key, str(value).replace('\n', '\n\t')))
                fp.write("%s\n" % (key))
            fp.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Gather jenkins inventory artifacts into a single inventory file")
    parser.add_argument("-j", "--jenkins", dest="jenkins",
                        default=os.getenv('JENKINS_URL', 'http://jenkins.testing.ansible.com'),
                        help="URL to Jenkins (default: %(default)s).")
    parser.add_argument("-u", "--user", dest="user",
                        default=os.getenv('JENKINS_USER', os.getenv('USER')),
                        help="Jenkins username (default: %(default)s).")
    parser.add_argument("-t", "--token", dest="token",
                        default=os.getenv('JENKINS_TOKEN'),
                        help="Jenkins API-Token.")
    parser.add_argument('--ini', action='store_true', default=False,
                        help='Output inventory in INI format (default: %(default)s)')
    parser.add_argument('--list', action='store_true', default=True,
                        help='List all hosts and groups (default: %(default)s)')
    parser.add_argument('--host', action='store',
                        help='Get all the variables about a specific instance')
    args = parser.parse_args()

    if args.jenkins is None or args.jenkins == "":
        parser.error("Must specify [-j|--jenkins].")
    if args.user is None or args.user == "":
        parser.error("Must specify [-u|--user].")
    if args.token is None or args.token == "":
        parser.error("Must specify [-t|--token].")

    return args


def download_url(url, verify=False, auth=None):
    r = requests.get(url, verify=verify, auth=auth)
    if r.status_code != http.client.OK:
        return None

    local_f = tempfile.NamedTemporaryFile(suffix='.ini', delete=False)
    try:
        for chunk in r.iter_content():
            local_f.write(chunk)
    finally:
        local_f.close()
    return local_f.name


if __name__ == "__main__":
    args = parse_args()

    if args.host:
        raise NotImplementedError("Coming soon")

    elif args.list:
        cfg = AnsibleInventory()
        master_inv = dict(_meta=dict(hostvars={}))

        for ansible_nightly_branch in ansible_nightly_branches:
            for platform in supported_platforms:
                for label in ['jenkins-gke-agent', ]:
                    # build URL to Jenkins artifact
                    url = urljoin(args.jenkins, job_path + artifact_path)
                    url = url.format(**dict(ansible_nightly_branch=ansible_nightly_branch, platform=platform, label=label))

                    # download artifact
                    local_inventory = download_url(url, verify=False, auth=(args.user, args.token))

                    # extend master_inv
                    if local_inventory:
                        try:
                            cfg.read(local_inventory)
                        except (configparser.MissingSectionHeaderError, configparser.ParsingError) as e:
                            sys.stderr.write("Failed to download inventory.log: %s\n" % url)

                        if has_ansible_v2:
                            class FakeOptions(object):
                                extra_vars = dict()

                            loader = DataLoader()
                            variable_manager = VariableManager()
                            variable_manager.extra_vars = load_extra_vars(loader=loader, options=FakeOptions())
                            inv_args = [loader, variable_manager]
                            inv_kwargs = dict(host_list=local_inventory)
                            get_groups = lambda x: x.get_groups().values()
                            get_group_vars = lambda x, y: x.get_group_variables(y)
                            # Workaround until fixed in `devel`
                            ansible.inventory.HOSTS_PATTERNS_CACHE = {}
                        else:
                            inv_args = [local_inventory, ]
                            inv_kwargs = {}
                            get_groups = lambda x: x.get_groups()
                            get_group_vars = lambda x, y: x.get_group_variables(y)

                        jenkins_inv = ansible.inventory.Inventory(*inv_args, **inv_kwargs)

                        # add group and hosts
                        for grp in get_groups(jenkins_inv):
                            # Initialize group dictionary
                            if grp.name not in master_inv:
                                master_inv[grp.name] = dict(hosts=[], vars={})
                            # Add group_vars
                            master_inv[grp.name]['vars'].update(get_group_vars(jenkins_inv, grp.name))
                            for host in grp.get_hosts():
                                # Add host to the group
                                if host.name not in master_inv[grp.name]['hosts']:
                                    master_inv[grp.name]['hosts'].append(host.name)
                                # Add hostvars
                                master_inv['_meta']['hostvars'][host.name] = host.vars

        if master_inv:
            if args.ini:
                cfg.write_ini(sys.stdout)
            else:
                print(json.dumps(master_inv, indent=2))
