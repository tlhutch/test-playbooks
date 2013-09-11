# ansibleworks-qa

This repository is a landing place for ansibleworks testing.  At present, it's not well organized.

## Notes

* Organizations
  * Inventories
    * Groups
      * Hosts
  * Teams
    * Credentials
    * Permissions
    * Users
      * Credentials
      * Permissions
* Projects
  * Playbooks
  * Job Templates
* Jobs

## Quickstart Procedure

For greater detail on the quickstart procedure, consult the [user guide](http://www.ansibleworks.com/releases/awx/docs/awx_user_guide.pdf).

1. Login
2. Create an Organization - `Bender Products Ltd.`
3. Create a new user and add the user to the organization - `dsmith`
   Also created org admin
4. Create a new inventory and add it to the organization - `Web Servers`
   Add group: CMS Web
5. Create a new set of credentials
   - root, ask password
6. Create a new project
   - ansible-examples, manual
   - ansible-examples, git+https
   - ansible-examples, git+ssh
   - ansible-examples, hg+https
   - ansible-examples, hg+ssh
7. Create a new Job Template
