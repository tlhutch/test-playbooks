## TODO
1. Simplify navigation through API without hard-coding
2. Research storing schema as json files (not .py)
3. Conslidate quickstart into a single suite, and use pytest_testsuite xfail plugin
4. Research building helpers within api object (related to #1)

## Outstanding questions

1. Why does adding a user to an org return no data '' and status_code=NO_CONTENT?
2. Why does the duplicate inventory json have *both* fields ['__all__', 'name']?
3. Why '/api/v1/inventory' and not '/api/v1/inventories'?
4. Why does '/api/v1/hosts' POST accept fields 'last_job' and 'last_job_host_summary'
5. Why are fields duplicated between job_template and job?  Isn't a job a execution of a template?
