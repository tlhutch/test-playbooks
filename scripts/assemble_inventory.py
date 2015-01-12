#!/usr/bin/env python

import os
import sys
import requests
import StringIO
import ConfigParser
import optparse
from urlparse import urljoin


class AnsibleInventory(ConfigParser.SafeConfigParser):
    def write(self, fp):
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
    parser = optparse.OptionParser()
    parser.add_option("-j", "--jenkins", dest="jenkins",
                      default=os.getenv('JENKINS_URL', 'http://50.116.42.103'),
                      help="URL to Jenkins (default: %default).")
    parser.add_option("-u", "--user", dest="user",
                      default=os.getenv('JENKINS_USER', os.getenv('USER')),
                      help="Jenkins username (default: %default).")
    parser.add_option("-t", "--token", dest="token",
                      default=os.getenv('JENKINS_TOKEN'),
                      help="Jenkins API-Token.")

    (opts, args) = parser.parse_args()

    if opts.jenkins is None or opts.jenkins == "":
        parser.error("Must specify [-j|--jenkins].")
    if opts.user is None or opts.user == "":
        parser.error("Must specify [-u|--user].")
    if opts.token is None or opts.token == "":
        parser.error("Must specify [-t|--token].")

    return (opts, args)


job_path = '/job/Test_Tower_Install/ANSIBLE_INSTALL_METHOD={ansible_install_method},PLATFORM={platform},label={label}/lastBuild'
artifact_path = '/artifact/playbooks/inventory.log/*view*/'
ansible_install_methods = ['stable', 'nightly']
supported_platforms = ['rhel-6.5-x86_64', 'centos-6.5-x86_64',
                       'centos-7.0-x86_64', 'rhel-7.0-x86_64',
                       'ubuntu-12.04-x86_64', 'ubuntu-14.04-x86_64']


if __name__ == "__main__":
    (opts, args) = parse_args()

    cfg = AnsibleInventory()

    for ansible_install_method in ansible_install_methods:
        for platform in supported_platforms:
            for label in ['test']:
                url = urljoin(opts.jenkins, job_path + artifact_path)
                url = url.format(**dict(ansible_install_method=ansible_install_method, platform=platform, label=label))
                r = requests.get(url, verify=False, auth=(opts.user, opts.token))
                try:
                    cfg.readfp(StringIO.StringIO(r.text))
                except (ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError) as e:
                    sys.stderr.write("Failed to download inventory.log: %s\n" % url)
                    continue

    if cfg.sections():
        cfg.write(sys.stdout)
    else:
        print "No usable inventory found."
