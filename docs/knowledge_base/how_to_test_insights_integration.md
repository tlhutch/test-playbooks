# Testing Insights Integration

You will find how to test Insights integration with Tower.

## Pre-requisites

Ensure that your Tower deployment has the `INSIGHTS_URL_BASE` configured. If
you are testing old Insights (Tower `<3.5`) integration it should be configured
to `https://access.redhat.com` if you are testing the new Insights (Tower
`3.5+`) integration it should be configured to `https://cloud.redhat.com`

Next you will need a host registered against Insights or you can mock it by
accessing the Insights web portal and finding a machine already registered in
there. See below how to find the machine ID and mock an Insights registration.

For the old Insights, go to inventory, find a machine and copy the UUID it
shows for the machine. For the new Insights, go to inventory, copy the UUID it
shows for the machine and make a request to
`https://cloud.redhat.com/api/inventory/v1/hosts/<UUID>`, then look for the
UUID shown on the `insights_id` field.

Once you have the Insights ID then create the
`/etc/redhat-access-insights/machine-id` and make sure its content is the
Insights ID with no new line. You can accomplish this by running the following
commands:

```
mkdir -p /etc/redhat-access-insights
echo -n <insights_id> > /etc/redhat-access-insights/machine-id
```

If you deployed locally using docker you can run the following:

```
docker exec --user=0 -it tools_awx_1 bash -c "mkdir -p /etc/redhat-access-insights; echo -n <insights_id > /etc/redhat-access-insights/machine-id"k
```

With that now your Tower host is a mocked Insights host.

## Collect and store the insights_id within Tower

In order to Tower recognize an host as an Insights host the host must have the
`insights_id` fact stored. To do that do the following:

* Create a SCM project that syncs https://github.com/ansible/awx-facts-playbooks.git
* Then create a job template that use that project and run against the desired inventory. It should run the `scan_facts.yml` playbook and have `Use Fact Cache` enabled.
  * For debugging purposes set the verbosity to 2 to see if it collected the insights machine id. This will be shown on the output of `Scan Insights for Machine ID (Unix/Linux)` task.
* Check if the insights system_id fact is present by going to Inventories > Your Inventory > Hosts > Your Host and then clicking on the Facts tab. The host should have the Insights `system_id` fact set.

## Setup an Insights project

* Create an Insights credential
* Create a Red Hat Insights project and make sure to use the created Insights
  credential. After saving the project make sure that its sync job succeeded.
* Go to Your Inventory and update the Insights Credential field to the one
  created on the first step. After saving the inventory, you should see a new
  button after the tabs, the `Remediate Inventory` button.
* Now if you click on the Hosts tab on Your Inventory details the host should
  have an `i` icon on its actions on the hosts list. Clicking on the `i` icon
  should pull the insights data for that host.
  * You can also fetch the Insights data of that host by going to the hosts
    details and then clicking on the Insights tab.

Doing the above should list the same number of actions you saw on Insights when
getting the machine ID. When seeing the Insights data of a given host you
should have two action buttons `View Data in Insights` and `Remediate
Inventory`. Clicking on the later should bring you to the New Job Template page
where you can choose which remediate playbook to run.

If you need more informaiton about this integration, you can check the [Ansible Tower Docs](https://docs.ansible.com/ansible-tower/latest/html/userguide/insights.html).

## Testing it locally

By doing the above steps over the UI you are already testing it via UI. If you
want to run the API tests then you can't do it locally. That is because there
is no `root` user on the local docker deployment container and therefore
running `pytest-ansible` adhoc commands won't work to create the `insights-id`
file.

Written by [Elyezer Rezende](mailto:erezende@redhat.com) (Github: elyezer) on April 22, 2019.
