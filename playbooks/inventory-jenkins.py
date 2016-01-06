#!/usr/bin/env python

import os
import sys
import json
import requests
import httplib
import argparse
import tempfile
import ConfigParser
import ansible.inventory
from urlparse import urljoin


job_path = '/job/Test_Tower_Install/PLATFORM={platform},label={label}/lastBuild'
artifact_path = '/artifact/playbooks/inventory.log/*view*/'
supported_platforms = ['rhel-6.7-x86_64', 'centos-6.latest-x86_64',
                       'centos-7.latest-x86_64', 'rhel-7.2-x86_64',
                       'ubuntu-12.04-x86_64', 'ubuntu-14.04-x86_64']


class AnsibleInventory(ConfigParser.SafeConfigParser):
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
    if r.status_code != httplib.OK:
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

        for platform in supported_platforms:
            for label in ['test']:
                # build URL to Jenkins artifact
                url = urljoin(args.jenkins, job_path + artifact_path)
                url = url.format(**dict(platform=platform, label=label))

                # download artifact
                local_inventory = download_url(url, verify=False, auth=(args.user, args.token))

                # extend master_inv
                if local_inventory:
                    try:
                        cfg.read(local_inventory)
                    except (ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError) as e:
                        sys.stderr.write("Failed to download inventory.log: %s\n" % url)

                    jenkins_inv = ansible.inventory.Inventory(local_inventory)

                    # add group and hosts
                    for grp in jenkins_inv.get_groups():
                        # Initialize group dictionary
                        if grp.name not in master_inv:
                            master_inv[grp.name] = dict(hosts=[], vars={})
                        # Add group_vars
                        master_inv[grp.name]['vars'].update(grp.get_variables())
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
                print json.dumps(master_inv, indent=2)
