import os

from towerkit.yaml_file import load_file

# load expected values for summary_fields user_capabilities
user_capabilities = load_file(os.path.join(os.path.dirname(__file__), 'user_capabilities.yml'))


def check_user_capabilities(resource, role):
    """Helper function used in checking the values of summary_fields flag, 'user_capabilities'"""
    assert resource.summary_fields['user_capabilities'] == user_capabilities[resource.type][role], \
        "Unexpected response for 'user_capabilities' when testing against a[n] %s resource with a user with %s permissions." \
        % (resource.type, role)
    # if given an inventory, additionally check child groups and hosts
    # child groups/hosts should have the same value for 'user_capabilities' as their inventory
    if resource.type == 'inventory':
        groups_pg = resource.get_related('groups')
        for group in groups_pg.results:
            assert group.summary_fields['user_capabilities'] == user_capabilities['group'][role], \
                "Unexpected response for 'user_capabilities' when testing groups with a user with inventory-%s." % role
        hosts_pg = resource.get_related('hosts')
        for host in hosts_pg.results:
            assert host.summary_fields['user_capabilities'] == user_capabilities['host'][role], \
                "Unexpected response for 'user_capabilities' when testing hosts with a user with inventory-%s." % role
