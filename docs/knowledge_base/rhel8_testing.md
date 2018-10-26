# RHEL8 Testing

RHEL 8 is supposed to be announced by the Red Hat summit in 2019.

Ansible Tower 3.5 will be our first version to be shipped with RHEL 8.

One can find RHEL 8 images at http://download-node-02.eng.bos.redhat.com/rel-eng/ (VPN is required).

*NOTE*: Python interpreter on the RHEL 8 nodes is located at `/usr/libexect/platform-python`.


## Testing timeline

  * `2018-10-24`: RHEL7 Tower node + RHEL8 Managed host - Status: `OK`

Tower: `3.3.0`
Ansible: `2.7.0`

Playbook:
```
---
- hosts: all
  tasks:
    - name: Display env
      command: env

    - name: Display Red Hat release
      command: cat /etc/redhat-release

    - name: Install vim
      become: True
      package:
        name: vim-minimal
```

Output:
```
Identity added: /tmp/awx_23_xI8k6j/credential_2 (/tmp/awx_23_xI8k6j/credential_2)
Using /etc/ansible/ansible.cfg as config file


PLAY [all] *********************************************************************

TASK [Gathering Facts] *********************************************************
ok: [10.41.11.102]

TASK [Display env] *************************************************************
changed: [10.41.11.102] => {"changed": true, "cmd": ["env"], "delta": "0:00:00.002089", "end": "2018-10-23 08:45:13.263576", "rc": 0, "start": "2018-10-23 08:45:13.261487", "stderr": "", "stderr_lines": [], "stdout": "LS_COLORS=\\nSSH_CONNECTION=10.41.11.160 59596 192.168.42.19 22\\n_=/usr/libexec/platform-python\\nLANG=en_US.UTF-8\\nXDG_SESSION_ID=8\\nUSER=cloud-user\\nSELINUX_ROLE_REQUESTED=\\nPWD=/home/cloud-user\\nHOME=/home/cloud-user\\nSSH_CLIENT=10.41.11.160 59596 22\\nSELINUX_LEVEL_REQUESTED=\\nSSH_TTY=/dev/pts/0\\nMAIL=/var/mail/cloud-user\\nSHELL=/bin/bash\\nSELINUX_USE_CURRENT_RANGE=\\nSHLVL=2\\nLOGNAME=cloud-user\\nDBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus\\nXDG_RUNTIME_DIR=/run/user/1000\\nPATH=/home/cloud-user/.local/bin:/home/cloud-user/bin:/usr/local/bin:/usr/bin\\nLESSOPEN=||/usr/bin/lesspipe.sh %s", "stdout_lines": ["LS_COLORS=", "SSH_CONNECTION=10.41.11.160 59596 192.168.42.19 22", "_=/usr/libexec/platform-python", "LANG=en_US.UTF-8", "XDG_SESSION_ID=8", "USER=cloud-user", "SELINUX_ROLE_REQUESTED=", "PWD=/home/cloud-user", "HOME=/home/cloud-user", "SSH_CLIENT=10.41.11.160 59596 22", "SELINUX_LEVEL_REQUESTED=", "SSH_TTY=/dev/pts/0", "MAIL=/var/mail/cloud-user", "SHELL=/bin/bash", "SELINUX_USE_CURRENT_RANGE=", "SHLVL=2", "LOGNAME=cloud-user", "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus", "XDG_RUNTIME_DIR=/run/user/1000", "PATH=/home/cloud-user/.local/bin:/home/cloud-user/bin:/usr/local/bin:/usr/bin", "LESSOPEN=||/usr/bin/lesspipe.sh %s"]}

TASK [Display Red Hat release] *************************************************
changed: [10.41.11.102] => {"changed": true, "cmd": ["cat", "/etc/redhat-release"], "delta": "0:00:00.002110", "end": "2018-10-23 08:45:13.744296", "rc": 0, "start": "2018-10-23 08:45:13.742186", "stderr": "", "stderr_lines": [], "stdout": "Red Hat Enterprise Linux release 8.0 Beta (Ootpa)", "stdout_lines": ["Red Hat Enterprise Linux release 8.0 Beta (Ootpa)"]}

TASK [Install vim] *************************************************************
ok: [10.41.11.102] => {"changed": false, "msg": "Nothing to do", "rc": 0, "results": ["Installed: vim-minimal"]}

PLAY RECAP *********************************************************************
10.41.11.102               : ok=4    changed=2    unreachable=0    failed=0 
```

