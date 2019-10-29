from awxkit import exceptions as exc
import pytest
import threading

from tests.api import APITest


@ pytest.mark.usefixtures('authtoken')
class TestInventorySource(APITest):

    def test_reject_invalid_credential_types_with_custom_source(self, factories):
        inventory = factories.inventory()
        org = inventory.ds.organization
        inv_script = factories.inventory_script(organization=org)

        kinds = ['vault', 'ssh', 'scm', 'insights']
        for kind in kinds:
            if kind == 'vault':
                cred = factories.credential(organization=org, kind=kind, inputs=dict(vault_password='fake'))
            else:
                cred = factories.credential(organization=org, kind=kind)

            error = 'Credentials of type machine, source control, insights and vault are disallowed for custom inventory sources.'
            with pytest.raises(exc.BadRequest) as e:
                factories.inventory_source(inventory=inventory, source_script=inv_script, credential=cred)
            assert error in str(e.value[1])

            inv_source = factories.inventory_source(inventory=inventory, source_script=inv_script)
            assert inv_source.source_script == inv_script.id
            with pytest.raises(exc.BadRequest) as e:
                inv_source.related.credentials.post(dict(id=cred.id))
            assert error in str(e.value[1])

    @pytest.mark.ansible_integration
    @pytest.mark.github('https://github.com/ansible/awx/issues/2240', skip=True)
    def test_imported_host_ordering(self, factories):
        inventory = factories.inventory()
        org = inventory.ds.organization
        inv_script = factories.inventory_script(
            organization=org,
            script=('\n'.join([
                '#!/usr/bin/env python',
                '# -*- coding: utf-8 -*-',
                'import json',
                '',
                '',
                'print(json.dumps({',
                '    "_meta": {',
                '        "hostvars": {',
                '            "h01": {}, "h02": {}, "h03": {}',
                '        }',
                '    },',
                '    "agroup": {',
                '        "hosts": ["h01", "h02", "h03"]',
                '    }',
                '}))'
            ]))
        )
        inv_source = factories.inventory_source(inventory=inventory, source_script=inv_script)
        assert inv_source.source_script == inv_script.id

        # Run the inventory update
        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()
        inv_hosts = inventory.related.hosts.get()
        assert inv_hosts.count == 3
        script_data = inventory.get_related('script')
        assert script_data['agroup']['hosts'] == ['h01', 'h02', 'h03']

    @pytest.mark.yolo
    @pytest.mark.ansible_integration
    def test_inventory_source_with_vaulted_vars(self, factories, ansible_version_cmp):
        # Feature was introduced in Ansible 2.6
        if ansible_version_cmp("2.6") < 0:
            pytest.skip("Not supported on Ansible versions predating 2.6.")

        # this is the string "artemis" encrypted with ansible-vault
        # direct output from:
        # ansible-vault encrypt_string --vault-id alan@prompt 'artemis'
        # (on prompt provide "password" for the vault password)
        # this command will give different numbers every time
        # so this exact string cannot be reproduced
        encrypted_content = (
            '$ANSIBLE_VAULT;1.2;AES256;alan\n'  # line break required, non-obvious Ansible-ism
            '61346130303231633133646133646639626338323565396239396633333736653630633938323733'
            '6235323735363362346632353132386466396232343133340a356330376131383637393535376236'
            '31383561616533643835336266366263346630666335336265306139316138666561626531313864'
            '3161633532623966380a333433303064383831613630366137656330353833383233353561626635'
            '3832'
        )

        # Create inventory source that puts the encrypted content in hostvars
        inventory = factories.inventory()
        org = inventory.ds.organization
        inv_script = factories.inventory_script(
            organization=org,
            script=('\n'.join([
                '#!/usr/bin/env python',
                '# -*- coding: utf-8 -*-',
                'import json',
                '',
                '',
                'print(json.dumps({',
                '    "_meta": {',
                '        "hostvars": {',
                '            "foobar": {',
                '                "encrypted_var": {',  # JSON object hooks used by Ansible
                '                    "__ansible_vault": """{}"""'.format(encrypted_content),
                '                }',
                '            }',
                '        }',
                '    },',
                '    "ungrouped": {',
                '        "hosts": ["foobar"]',
                '    }',
                '}))'
            ]))
        )
        inv_source = factories.inventory_source(inventory=inventory, source_script=inv_script)
        assert inv_source.source_script == inv_script.id

        # Run the inventory update
        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()
        inv_hosts = inventory.related.hosts.get()
        assert inv_hosts.count == 1
        host = inv_hosts.results.pop()
        assert 'encrypted_var' in host.variables
        assert host.variables.encrypted_var['__ansible_vault'] == encrypted_content

        # Decrypt vault secret by running a playbook
        vault_cred = factories.credential(
            kind='vault', organization=org,
            inputs=dict(
                vault_password='password',
                vault_id='alan'
            )
        )
        jt = factories.job_template(playbook='debug_hostvars.yml', inventory=inventory)
        jt.add_credential(vault_cred)
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert '"encrypted_var": "artemis"' in job.result_stdout

    def test_conflict_exception_with_running_inventory_update(self, factories):
        inv_source = factories.inventory_source()
        inv_update = inv_source.update()

        with pytest.raises(exc.Conflict) as e:
            inv_source.delete()
        assert e.value[1] == {'error': 'Resource is being used by running jobs.', 'active_jobs': [{'type': 'inventory_update', 'id': inv_update.id}]}

        inv_source.wait_until_completed().assert_successful()
        inv_update.get().assert_successful()

    def update_and_delete_resources(self, inv_source):
        inv_source.update().wait_until_completed().assert_successful()

        groups = inv_source.get_related('groups')
        hosts = inv_source.get_related('hosts')

        # Add all instances to newly created instance group, in parallel
        # Past issues seen include:
        # 504 timeout - deletion of groups is too heavy, request times out
        # 500 error - deadlock because groups and host deletes conflict
        threads = [
            threading.Thread(target=groups.delete),
            threading.Thread(target=hosts.delete)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with pytest.raises(exc.NotFound):
            groups.results[0].get()  # canary, actual groups span multiple pages
        with pytest.raises(exc.NotFound):
            hosts.results[0].get()
        assert groups.get().count == 0
        assert hosts.get().count == 0

    def test_delete_sublist_resources(self, factories):
        inv_source = factories.inventory_source()
        self.update_and_delete_resources(inv_source)

    def test_simultaneous_delete_sublist_resources_generic_large_inventory(self, factories):
        Ng = 470
        Nh = 189
        # In this inventory, all hosts are members of all groups,
        # so that makes it more challenging to avoid conflicts while deleting both
        inv_source = factories.inventory_source(
            source_script=factories.inventory_script(
                script='\n'.join([
                    "#!/usr/bin/env python",
                    "import json",
                    "hosts=['Host-{}'.format(i) for i in range(%s)]" % Nh,
                    "data = {'_meta': {'hostvars': {}}}",
                    "for i in range(%s):" % Ng,
                    "   data['Group-{}'.format(i)] = {'hosts': hosts}",
                    "print(json.dumps(data, indent=2))"
                ])
            )
        )
        self.update_and_delete_resources(inv_source)

    def test_simultaneous_delete_sublist_resources_ec2(self, factories):
        # Reported custom issue where server error, deadlocks, occured
        inv_source = factories.inventory_source(
            source='ec2',
            credential=factories.credential(kind='aws')
        )
        self.update_and_delete_resources(inv_source)
