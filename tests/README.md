ansibleworks-qa tests
---------------------

# Instructions

1. Create, and modify, `credentials.yaml`
    cp credentials.template credentials.yaml
    vim credentials.yaml
2. Determine URL for running AWX instance (needed by `--api-baseurl` parameter)
3. Run tests:
    PYTHONPATH=tests/lib py.test --api-baseurl https://example.com  --destructive tests

# TODO

1. Completed SCM tests
2. Research storing schema as json files (not .py)
3. Testing cloud inventory
   * jobs should wait until inventory sync is complete
4. Test RBAC authentication+permissions
5. Test SCM projects
6. Build basic UI navigation test (capable of offloading to SauceLabs for browser compatability testing)

# Unittest gaps

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

# Open Questions
1. Delete credentials, but they remain attached to jobs ... and available for use
2. Credentials filtering and __in (comma or list)?
   - Searching for names with a ',' in them
3. The API doesn't always handle converting null values into empty string ''
   - Example, creating a project with scm_type=null ... should produce a project with scm_type=''
