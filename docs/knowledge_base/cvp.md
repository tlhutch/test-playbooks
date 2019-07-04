# Continuous Verification Pipeline (CVP)

Within Red Hat there is an effort for the containers published on the [Red Hat Containers Catalog](https://access.redhat.com/containers/) (RHCC) to be always scored A.

More information on how the health index grades works can be found at https://access.redhat.com/articles/2803031

The effort resulted in the creation of 4 new tools that aims to make it possible to automatically release new version of our containers based on CVE releases:

  * [FreshMaker](#freshmaker)
  * [Botas](#botas)
  * [CVP](#cvp)
    * [Ansible Tower QE and CVP Integration](#ansible-tower-qe-and-cvp-integration)
  * [Release Driver](#release-driver)

## FreshMaker

[FreshMaker](https://mojo.redhat.com/docs/DOC-1155261) is an internal tool, that once a CVE has been fixed and a new version of an impacted packages released, will scan for all containers containing this packages (or inheriting from a container containing this package) and trigger a new brew build of them.

## Botas

[Botas](https://mojo.redhat.com/docs/DOC-1155261) is a service responsible for automated advisory creation for container builds with CVE fixes done by Freshmaker.

## CVP

The [Continuous Verification Pipeline (CVP)](https://docs.engineering.redhat.com/spaces/viewspace.action?key=CVP) aims to provide QE teams a way to have a say whether the automatically rebuilt container should be released or not.

CVP allows QE team to enable testing of the containers at two level:

  * Individually: By allowing one to run functionnal test on individual container (when it applies) and be able to submit results back to [ResultsDB](https://resultsdb.engineering.redhat.com/results)
  * GroupTesting: One's application might require to be tested with the full application set of containers it will be deployed with. This is call group testing. CVP provides a way for QE team to test a set of container and submit results back to [ResultsDB](https://resultsdb.engineering.redhat.com/results).

More on their [confluence page](https://docs.engineering.redhat.com/spaces/viewspace.action?key=CVP)

### Ansible Tower QE and CVP Integration

The Ansible Tower QE team has set a [CVP Listener job](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/cvp-listener/) that will listen to the GroupTesting event. Once an event has been detected it will automatically trigger the [CVP Validator pipeline]() that is in charge of parsing the data submitted in the event and call the [OpenShift Install and Integration pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Pipelines/job/openshift-integration-pipeline/) with the proper set of parameters (ie. proper set of containers to test together). Once this jobs end the proper results is submitted back to [ResultsDB](https://resultsdb.engineering.redhat.com/results).

**Note**: At this point the Ansible Tower QE team did not enable the `auto-release` knob in [Comet](https://comet.engineering.redhat.com/containers/products), so containers won't be automatically released. Plan is to go with Slack notification for the first few iterations, and once the team feels confident enough about this process enable the option.

**Note2**: For testing purpose one can simulate a GroupTesting event by triggering this [job](http://jenkins.ansible.eng.rdu2.redhat.com/job/qe-sandbox/job/spredzy/job/cvp-trigger-pipeline/).

## Release driver

[release-driver](https://mojo.redhat.com/docs/DOC-1155261) is a service responsible for automatically shipping botas advisories that make it to the `REL_PREP` state.
