# ansibleworks-qa tests

## Instructions

1. Install test requirements

        pip install -r requirements.txt

2. Create, and modify, `credentials.yml`

        cp credentials.template credentials.yml
        vim credentials.yml  # update as needed

3. Determine URL for running AWX instance (needed by `--baseurl` parameter)
4. Disable ansible host key checking

        export ANSIBLE_HOST_KEY_CHECKING=False

5. Run the tests:

        py.test --baseurl https://example.com --destructive tests

## TODO

1. Model comprehensive RBAC test scenario
1. Comprehensive performance scenarios

## Unittest gaps

The following list was produced with help from the API development team to identify areas where API unittest coverage needs to be supplimented with integrated tests.

1. Anything that drives celery jobs should be covered on installed system
2. RBAC coverage and permissions
3. job_template callbacks
   - test for matching inventory <IP>
   - test for matching inventory ansible_ssh_host=<IP>
   - test for matching inventory by reverse lookup of <IP>
   - test for matching inventory by forward lookup for each host in the inventory, looking for a matching <IP>
   - test callback from a server not in inventory
4. Upgrades
5. Inventory_source with update_on_launch and a project with update_on_launch
   - Should see job.status == 'waiting'
