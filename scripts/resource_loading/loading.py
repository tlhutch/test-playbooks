from argparse import ArgumentParser
import os

from towerkit import config, utils, yaml_file
from ansible.parsing.dataloader import DataLoader
try:
    from ansible.vars import VariableManager
    from ansible.inventory import Inventory
    ansible_24 = False
except ImportError:
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    ansible_24 = True


def delete_all(endpoint):
    resource = endpoint
    while True:
        resource = resource.get()
        for item in resource.results:
            try:
                item.delete()
            except Exception as e:
                print(e)
        if not resource.next:
            return


def delete_all_created(v1):
    for endpoint in (v1.jobs, v1.job_templates, v1.projects, v1.inventory, v1.inventory_scripts,
                     v1.credentials, v1.teams, v1.users, v1.organizations):
        delete_all(endpoint)


cwd = os.path.dirname(__file__)

parser = ArgumentParser()
_inv_help = 'Inventory file with instance in "tower" group (default: playbooks/inventory.log)'
parser.add_argument('--inventory', dest='inventory', help=_inv_help,
                    default=os.path.join(cwd, '..', '..', 'playbooks/inventory.log'))

_cred_help = 'Credential file to be loaded (default: config/credentials.yml).  Use "false" for none.'
parser.add_argument('--credentials', dest='credentials', help=_cred_help,
                    default=os.path.join(cwd, '..', '..', 'config/credentials.yml'))

_resource_help = 'Resource file to be loaded (default: scripts/resource_loading/data.yml)'
parser.add_argument('--resources', dest='resources', help=_resource_help,
                    default=os.path.join(cwd, 'data.yml'))

_azure_help = "Don't fail if azure-related inventory resources are missing."
parser.add_argument('--no-azure', dest='no_azure', action='store_true', help=_azure_help)
args = parser.parse_args()

loader = DataLoader()

if ansible_24:
    variable_manager = VariableManager(loader=loader)
    inventory_manager = InventoryManager(loader=loader, sources=args.inventory)
else:
    inventory_manager = Inventory(loader=loader, variable_manager=VariableManager(), host_list=args.inventory)

resources = utils.PseudoNamespace(yaml_file.load_file(args.resources))

try:
    group = [potential for potential in ['tower'] if potential in inventory_manager.groups][0]
except IndexError:
    raise Exception('{0.inventory} is without desired "tower" group.'.format(args))

config.base_url = "https://{0}".format(inventory_manager.groups[group].hosts[0].address)

if utils.to_bool(args.credentials):
    config.credentials = utils.load_credentials(args.credentials)
