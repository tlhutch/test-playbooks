#!/usr/bin/env python

import sys
import requests
import StringIO
import ConfigParser

class AnsibleInventory(ConfigParser.SafeConfigParser):
    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
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

user = 'jlaska'
password = 'd6733c68ed00072ee47822c16af14662'
base_url = 'http://50.116.42.103/'
job_path = 'job/Test_Tower_Install/CLOUD_PROVIDER={cloud_provider},PLATFORM={platform},label={label}/lastBuild/'
artifact_path = 'artifact/playbooks/inventory.log/*view*/'

cfg = AnsibleInventory()

for cloud_provider in ['rax', 'ec2']:
    for platform in ['rhel-6.5-x86_64', 'centos-6.5-x86_64', 'rhel-7.0-x86_64', 'ubuntu-12.04-x86_64', 'ubuntu-14.04-x86_64']:
        for label in ['test']:
            url = base_url + job_path + artifact_path
            url = url.format(**dict(cloud_provider=cloud_provider, platform=platform, label=label))
            r = requests.get(url, verify=False, auth=(user, password))
            try:
                cfg.readfp(StringIO.StringIO(r.text))
            except (ConfigParser.MissingSectionHeaderError, ConfigParser.ParsingError) as e:
                sys.stderr.write("Failed to download inventory.log: %s\n" % url)
                continue

if cfg.sections():
    cfg.write(sys.stdout)
else:
    print "No usable inventory found."
