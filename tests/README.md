ansibleworks-qa tests
---------------------

# Instructions

1. Create, and modify, `credentials.yaml`
    cp credentials.template credentials.yaml
    vim credentials.yaml
2. Determine URL for running AWX instance (needed by `--baseurl` parameter)
3. Run tests:
    PYTHONPATH=tests/lib py.test -v --baseurl https://example.com tests/api/quickstart --destructive

## TODO
1. Research storing schema as json files (not .py)
2. Research building helpers within api object (related to #1) (similar to mozwebqa page objects)
   * GOAL: use the same names regardless of whether testing the API or the UI
   * api.organizations.[get, put, post, patch, options, delete] ? ... perhaps too atomic
   * api.organizations.[create, delete, update] ?
3. Testing cloud inventory
   * jobs should wait until inventory sync is complete
4. Testing RBAC
5. React to credential changes
6. Figure out how to pass along SSH credentials

## Outstanding questions

1. Why does adding a user to an org return no data '' and status_code=NO_CONTENT?
2. Why does the duplicate inventory json have *both* fields ['__all__', 'name']?
3. Why '/api/v1/inventory' and not '/api/v1/inventories'?
4. Why does '/api/v1/hosts' POST accept fields 'last_job' and 'last_job_host_summary'
5. Why are fields duplicated between job_template and job?  Isn't a job a execution of a template?

