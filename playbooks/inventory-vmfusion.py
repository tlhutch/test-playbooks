#!/usr/bin/env python
import os
import sys
import subprocess
import re
import string
import json
import argparse


VMRUN = os.getenv('VMRUN', '/Applications/VMware Fusion.app/Contents/Library/vmrun')


def parse_args():
    parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on VMware Fusion')
    parser.add_argument('--list', action='store_true', default=True,
                       help='List instances (default: True)')
    parser.add_argument('--host', action='store',
                       help='Get all the variables about a specific instance')
    return parser.parse_args()


def get_vm_ip(vmxfile):
    """Return the IP of a running VM"""
    try:
        ip = subprocess.check_output([VMRUN, 'getGuestIPAddress', vmxfile]).strip()
        return ip
    except Exception as error:
        return None


def get_running_vms():
    """List the running VMs"""
    output = subprocess.check_output( [VMRUN, "list"]).split('\n')

    vms = []

    for line in output:
        matcher = re.search("\.vmx$", line)
        if matcher:
            vms.append(matcher.string)

    return vms


if __name__ == "__main__":
    if not os.path.exists(VMRUN):
        print("Unable to locate vmrun application")
        sys.exit(1)

    args = parse_args()

    # TODO: add --host support
    if args.host:
        print("WARNING: this doesn't do anything yet")
        # initialize inventory
        inventory = dict()

    elif args.list:

        # initialize inventory
        inventory = dict(fusion=[])

        # gather VMs
        for vm in get_running_vms():
            vm_ip = get_vm_ip(vm)
            if vm_ip is not None:
                inventory['fusion'].append(vm_ip)

        # hostvars
        inventory['_meta'] = dict(hostvars={})
        for host in inventory.get('fusion', []):
            inventory['_meta']['hostvars'][host] = dict(ansible_user='root')

    print(json.dumps(inventory))
