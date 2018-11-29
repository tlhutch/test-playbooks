# How to provision dev Tower standalone instances

This document will walk you through the process of provisioning a dev Tower
standalone instance using the [Test_Tower_Install](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Install) Jenkins job.

## Building the job to start the deployment

The Test_Tower_Install job is used by the automation job primarily but you can
use it to deploy personal dev deployments that run on AWS. To do this go to the
job page and click on `Build with Parameters`. In this next page, you need to
edit some fields: `TOWERQA_GIT_BRANCH`, `TRIGGER`, `INSTANCE_NAME_PREFIX`, and
`AW_REPO_URL`.

The `TOWERQA_GIT_BRANCH` and `AW_REPO_URL` need to be edited only when you want
to deploy a version other than devel. To deploy a specific version you have to
replace `devel` with a relase branch, such as `release_3.3.2.` on both fields.

The `TRIGGER` field indicates that the job should trigger the job that runs the
integration tests. In the case of a dev Tower deployment this field should
unchecked.

It is important to edit the `INSTANCE_NAME_PREFIX` because otherwise it may
delete instances being used by the automation jobs. We usually use our names or
usernames as the value for this field. Having a name prefix helps anyone
looking on the AWS instances to identify instance owners and query them in case
they need to stop/remove those instances.

The last step is to select the deployment permutations you want. Check the
`config` table and click on `None` to unselect all the permutations. After
that, select the permutations you want. Usually it should be one permutation,
like the latest RHEL and the latest Ansible Core version supported.

Once all the above configuration is done, you can go ahead and click on the
`Build` button. It will trigger the job and start deploying your dev Tower
instance.

## Checking the job for the generated artifacts

Considering that you already triggered the deployment (see the previous section
for more information) and it has completed successfuly. You can check the job
result and look for the generated artifacts, you may be interested on the
inventory that the job created. The inventory will allow you run tower-qa tests
against your deployment.

To view the generated inventory you need to access the related job details and
it will present a table similar to the one you had when triggering the job.
Then you can click on the deployment permutation you selected to check its
details. On the deployment permutation details page you can access the
inventory by clicking on `inventory.log` that is available within the `Build
Artifacts` section. Then you can copy the inventory contents into your local
`playbooks/inventory` file and run you tests.

## Additional notes

Be aware that there is a nightly job that clean up running instances on AWS.
That means if you can't access your deployment anymore on the next day it is
probably because that job and then you need to deploy a new instance.

Written by [Elyézer Rezende](mailto:erezende@redhat.com) (Github: elyezer) Nov 29, 2018.
