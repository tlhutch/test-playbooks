# How to test compatibility with RHEL pre-releases

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Versions of Tower to test](#versions-of-tower-to-test)
- [Automated Process](#automated-process)
- [Reference](#reference)

## Overview

When RHEL approaches the end of a release, it will cut an alpha and beta image. When each image is available, an e-mail is sent out to other Red Hat product groups, prompting the groups to pull the RHEL image, install their product on the platform, and confirm their product remains functional on the new platform. In general, interoperability testing with the alpha image is optional, while testing against the beta image is mandatory.

More infos available in this presentation:

  * Bluejeans: https://bluejeans.com/s/DhW@w
  * Slides: https://docs.google.com/presentation/d/14T38IbMMMC6JBBbhKcFf7RXTu7xT2mBPZeQ7NM34rZg/edit?usp=sharin


## Prerequisites

* The Compose ID of the RHEL version to test. It is made available to you on the JIRA ticket linked in the email sent out prompting for testing.


## Versions of Tower to test

* The RHEL pre-release image should be tested with each [currently supported version of Tower](https://access.redhat.com/support/policy/updates/ansible-tower).


## Automated Process

The [Layered Product Testing]() pipeline will do everything required to perform the proper operation. Simply trigger it and if the pipeline is succesful reports PASS to the Jira ticket.

In a nutshell the pipeline does the following step:

  1. Prepare the environment
  2. Spawn a VM on our [OpenStack](https://rhos-d.infra.prod.upshift.rdu2.redhat.com/dashboard/auth/login/) tenant with the desired Compose ID
  3. Install Ansible Tower on it with the specified version
  4. Run a subset of test to ensure proper operation are functional

Those 4 steps are run for all the [currently supported version of Tower](https://access.redhat.com/support/policy/updates/ansible-tower).


# Reference

* RHEL Layered Product Interoperability Testing Information Session - ([Slides](https://docs.google.com/presentation/d/14T38IbMMMC6JBBbhKcFf7RXTu7xT2mBPZeQ7NM34rZg/edit#slide=id.gb6f3e2d2d_2_207)) ([Recording](https://bluejeans.com/s/DhW@w))
* [RHEL 6, 7, 8 Interoperability testing spreadsheet (Test Status)](https://docs.google.com/spreadsheets/d/1nLRLxubSlctsyVIlkW6Kbob0kSqQYDNxbbx30rwg82w/edit#gid=1416156808)
* [RHEL 8.0 Interop Dashboard (Confluence)](https://docs.engineering.redhat.com/display/PIT/RHEL+8.0+Interop+Dashboard)
* [RHEL Layered Product Interoperability Testing (Confluence)](https://docs.engineering.redhat.com/display/PIT/RHEL+Layered+Product+Interoperability+Testing)
* [QE Product Interop Testing Group (Mojo)](https://mojo.redhat.com/groups/qe-product-interop-testing)

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Oct 5, 2018.
