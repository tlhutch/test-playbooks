import logging
import os

from awxkit.yaml_file import load_file
import pytest

log = logging.getLogger(__name__)

SUPPORTED_INV_SOURCES = ('ec2', 'azure_rm', 'gce', 'openstack')


@pytest.fixture(scope="session")
def inventory_schema():
    def _load_schema_file(inv_source):
        return load_file(os.path.join(os.path.dirname(__file__),
                         'static/inventory_source_schema/{}.yml'.format(inv_source)))
    return {inv_source: _load_schema_file(inv_source)
            for inv_source in SUPPORTED_INV_SOURCES}


@pytest.fixture(scope="function")
def inventory_hostvars(inventory_schema):
    """Return map to each inventory type's expected hostvars when run in compatibility mode.

    These are what we consider a minimum acceptable set of hostvars that each host should have defined.
    """
    return {inv_source:inventory_schema[inv_source]['hostvars']
            for inv_source in SUPPORTED_INV_SOURCES}


def _emulate_core_sanitization(s):
    result = ""
    for letter in s:
        if letter == ' ':
            result += '_'
        elif ord(letter) < 128:
            result += letter
        else:
            result += '_'

    return result


@pytest.fixture(scope="function")
def hostvars_that_create_groups():
    return {
        'ec2': {
                'ec2_placement': lambda x: x,
                'ec2_region': lambda x: x,
                'ec2_vpc_id': lambda x: 'vpc_id_{}'.format('_'.join([word for word in x.split('-')])),
                'ec2_security_group_names': lambda x: 'security_group_{}'.format('_'.join([word for word in x.split('-')])),
               },
        'gce': {
                   'gce_zone': lambda x: x,
                   'gce_status': lambda x: 'status_{}'.format(x.lower()),
                   'gce_tags': lambda x: f'tag_{x}',
               },

        'azure_rm': {
                # note this is only if these are enabled via source vars
                'tags': lambda x: '_'.join(_emulate_core_sanitization(word) for word in x.split()),
               }
        }


@pytest.fixture(scope="function")
def hostvars_that_create_host_names():
    return {
        'ec2': ['ec2_ip_address', 'ec2_dns_name'],
        'gce': ['gce_name'],
        'azure_rm': ['computer_name']  # also name
    }


@pytest.fixture(scope="function")
def inventory_hostgroups(inventory_schema):
    """Return map to each inventory type's expected groups created when run in compatibility mode.

    These are what we consider a minimum acceptable set of groups that each inventory should create on import.

    Note these groups are generated dynamically from values in hostvars, so our expectations are pretty low
    and still could be effected by changes in the environment.

    If a test began to fail because of these groups missing, it would also be prudent to look to see if the
    hostvar that would provide the data is present.
    """
    return {inv_source:inventory_schema[inv_source]['hostgroups']
            for inv_source in SUPPORTED_INV_SOURCES}
