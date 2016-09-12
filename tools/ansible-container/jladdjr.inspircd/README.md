Role Name
=========

This role installs and configures an [InspIRCd](http://www.inspircd.org) IRC server using a minimal set of configuration options.

Requirements
------------

* Must run as root (Note: Role creates new non-root user, installs / runs server under new user)
* Only EL7 systems supported at this time

Role Variables
--------------

The following defaults are found in [defaults/main.yml](defaults/main.yml):

```yaml
# Inspircd user
inspircd_user: "irc"

# Path where inspircd is installed
inspircd_install_dir: "/usr/local/src/inspircd"

# inspircd branch to install from (insp20 => latest stable)
inspircd_branch: insp20
```

Configuration information for the server address and admin user
are stored in [vars/main.yml](vars/main.yml):

```yaml
---
# Admin user
inspircd_admin_real_name: "IRC Admin"
inspircd_admin_nick: "admin"
inspircd_admin_email: "admin@domain.com"

# IRC Server Bind Information
inspircd_bind_address: "*"
inspircd_bind_port: "6667"

# Power passwords (for halting / restarting server)
inspircd_power_die_password: "FIXME"
inspircd_power_restart_password: "FIXME"

# Message of the Day
inspircd_motd: "-- Welcome! ---"

# Operator Privileges
inspircd_operator_password: "FIXME"
```

Dependencies
------------

None

Example Playbook
----------------

```yaml
    - hosts: servers
      roles:
      - role: inspircd
        inspircd_power_die_password: "<password>"
        inspircd_power_restart_password: "<password>"
        inspircd_operator_password: "<password>"
```

Deploying container from role
-----------------------------

[Ansible Container](https://www.ansible.com/ansible-container) creates
Docker containers based on Ansible roles. Point ansible-container to the
[ansible](ansible/) directory to create an IRC server from this role.

Note: At the time of writing, the role may need to be located inside the
ansible directory in order for ansible-container to find the role.

License
-------

BSD

Author Information
------------------

James Ladd, Jr.
