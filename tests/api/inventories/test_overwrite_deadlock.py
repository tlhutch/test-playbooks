import os

import pytest

from tests.api import APITest


CUSTOM_SCRIPT = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import uuid
unique_name = str(uuid.uuid4())
host_1 = 'host_{}'.format(unique_name)
host_2 = 'host_2_{}'.format(unique_name)
print(json.dumps({
'_meta': {'hostvars': {
    '{}'.format(host_1): {'name':'{}'.format(host_1)},
    '{}'.format(host_2): {'name':'{}'.format(host_2)},
    'all_have': {'name':'all_have'},
    'all_have2': {'name':'all_have2'},
    'all_have3': {'name':'all_have3'},
    }},
'ungrouped': {'hosts': ['groupless']},
'child_group': {'hosts': ['{}'.format(host_1), 'all_have']},
'child_group2': {'hosts': ['{}'.format(host_1), 'all_have2']},
'parent_group': {'hosts': ['{}'.format(host_2), 'all_have3'], 'children': ['child_group', 'child_group2']}
}))"""


DELETE_GROUP_1_CUSTOM_SCRIPT = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import uuid
unique_name = str(uuid.uuid4())
host_1 = 'host_{}'.format(unique_name)
host_2 = 'host_2_{}'.format(unique_name)
print(json.dumps({
'_meta': {'hostvars': {
    '{}'.format(host_1): {'name':'{}'.format(host_1)},
    '{}'.format(host_2): {'name':'{}'.format(host_2)},
    'all_have': {'name':'all_have'},
    'all_have2': {'name':'all_have2'},
    'all_have3': {'name':'all_have3'},
    }},
'child_group2': {'hosts': ['{}'.format(host_1), 'all_have2']},
'parent_group': {'hosts': ['{}'.format(host_2), 'all_have3'], 'children': ['child_group2']}
}))"""


DELETE_GROUP_2_CUSTOM_SCRIPT = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import uuid
unique_name = str(uuid.uuid4())
host_1 = 'host_{}'.format(unique_name)
host_2 = 'host_2_{}'.format(unique_name)
print(json.dumps({
'_meta': {'hostvars': {
    '{}'.format(host_1): {'name':'{}'.format(host_1)},
    '{}'.format(host_2): {'name':'{}'.format(host_2)},
    'all_have': {'name':'all_have'},
    'all_have2': {'name':'all_have2'},
    'all_have3': {'name':'all_have3'},
    }},
'child_group': {'hosts': ['{}'.format(host_1), 'all_have']},
'parent_group': {'hosts': ['{}'.format(host_2), 'all_have3'], 'children': ['child_group']}
}))"""


DELETE_GROUP_3_CUSTOM_SCRIPT = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import uuid
unique_name = str(uuid.uuid4())
host_1 = 'host_{}'.format(unique_name)
host_2 = 'host_2_{}'.format(unique_name)
print(json.dumps({
'_meta': {'hostvars': {
    '{}'.format(host_1): {'name':'{}'.format(host_1)},
    '{}'.format(host_2): {'name':'{}'.format(host_2)},
    'all_have': {'name':'all_have'},
    'all_have2': {'name':'all_have2'},
    'all_have3': {'name':'all_have3'},
    }},
'child_group': {'hosts': ['{}'.format(host_1), 'all_have']},
'child_group2': {'hosts': ['{}'.format(host_1), 'all_have2']},
}))"""


@pytest.mark.usefixtures('authtoken')
class TestInventoryUpdateOverlappingSources(APITest):

    @pytest.mark.yolo
    def test_update_with_overwrite_attempt_deadlock(self, v2, factories):
        """Update an inventory with multiple sources that update same groups and hosts.'

        In past, this could result in bad clobbering behavior or a database lock.
        See https://github.com/ansible/tower/issues/3212.

        The number of inventory sources is configurable because the race
        condition is more reliably reproduced with a larger number of inventory
        sources.

        For example, running this test with 20 iventory sources against tower
        3.4.3 resulted in 7/20 failing with a deadlock on deleting groups.

        A different deadlock involving hosts was experienced in 3.4.0 with as
        few as 3 inventories with shared hosts.
        """
        source_scripts = []
        inv_sources = []
        shared_org = factories.organization()
        shared_parent_inv = factories.inventory(organization=shared_org)
        NUM_INV_SOURCES = int(
            os.environ.get(
                'TOWERQA_NUM_INVENTORY_SOURCES_OVERWRITE_DEADLOCK', 3))
        if not NUM_INV_SOURCES:
            pytest.skip(
                'Set TOWERQA_NUM_IVENTORY_SOURCES_OVERWRITE_DEADLOCK to a positive integer to run test')
        for i in range(NUM_INV_SOURCES):
            inv_script = factories.inventory_script(
                script=CUSTOM_SCRIPT,
                organization=shared_org,
            )
            inv_source = factories.inventory_source(
                overwrite=True,
                overwrite_vars=True,
                source_script=inv_script,
                organization=shared_org,
                inventory=shared_parent_inv
            )
            assert inv_source.source_script == inv_script.id
            source_scripts.append(inv_script)
            inv_sources.append(inv_source)
            inv_source.update().wait_until_completed().assert_successful()
        shared_parent_inv = shared_parent_inv.get()
        assert shared_parent_inv.total_inventory_sources == NUM_INV_SOURCES, "Not all sources were added correctly from independently run updates"
        # Now try and update all inventories simultaneously
        # in the past would have run into database lock from race on shared groups and hosts
        updates = shared_parent_inv.related.update_inventory_sources.post()
        for update in updates:
            update_page = v2.inventory_updates.get(id=update['id']).results.pop()
            update_page.wait_until_completed().assert_successful()

        shared_parent_inv = shared_parent_inv.get()
        # Each has 2 unique hosts
        # Then the three invs all share 4 other hosts, all_have, all_have2, all_have3, and groupless
        EXPECTED_TOTAL_HOSTS = (NUM_INV_SOURCES * 2) + 4
        EXPECTED_GROUP_HOSTS = NUM_INV_SOURCES + 1
        assert shared_parent_inv.total_hosts == EXPECTED_TOTAL_HOSTS, 'Each source has a unique host and there are 4 shared hosts'
        assert shared_parent_inv.total_groups == 3, 'Should have had parent group, child_group, and child_group2'
        # make assertions about group membership
        groups = shared_parent_inv.related.groups.get().results
        for group in groups:
            assert group.name in ['child_group', 'child_group2', 'parent_group']
            hosts = group.related.hosts.get().results
            host_names = [host.name for host in hosts]
            assert len(hosts) == EXPECTED_GROUP_HOSTS, 'Expected one unique host from each inventory and one shared group host'
            if group.name == 'child_group':
                assert 'all_have' in host_names
            if group.name == 'child_group2':
                assert 'all_have2' in host_names
            if group.name == 'parent_group':
                assert 'all_have3' in host_names
            for host in hosts:
                assert host.name == host.related.variable_data.get()['name']
        for i, source in enumerate(inv_sources):
            if i % 3 == 0:
                inv_script = factories.inventory_script(
                    script=DELETE_GROUP_1_CUSTOM_SCRIPT,
                    organization=shared_org,
                    )
                source.source_script = inv_script.id
            if i % 3 == 1:
                inv_script = factories.inventory_script(
                    script=DELETE_GROUP_2_CUSTOM_SCRIPT,
                    organization=shared_org,
                    )
                source.source_script = inv_script.id
            if i % 3 == 2:
                inv_script = factories.inventory_script(
                    script=DELETE_GROUP_3_CUSTOM_SCRIPT,
                    organization=shared_org,
                    )
                source.source_script = inv_script.id

        updates = shared_parent_inv.related.update_inventory_sources.post()
        for update in updates:
            update_page = v2.inventory_updates.get(id=update['id']).results.pop()
            update_page.wait_until_completed().assert_successful()
