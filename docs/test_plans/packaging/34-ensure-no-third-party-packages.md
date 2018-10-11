
Source all Packages from ansible.releases.com
---------------------------------------------

see: https://github.com/ansible/tower/issues/671

With Tower 3.4, we will source all packages from ansible.release.com or RHEL repos.
No longer will packages be pulled from 3rd party repositories or EPEL.

Updates from prior Tower versions to Tower 3.4 should also have all 3rd party
packages removed and replaced with packages from approved sources.

Test Plan
----------

- [ ] Run installer to install Tower on fresh AMI in EC2 (RHEL 7.5)
  - [ ] Ensure that no third party packages are present.
         The following shell command should output any third party packages:
        ```
        yum list installed 2>/dev/null | \
        grep -v "ansible" | grep -v "anaconda" | \
        grep -v "@rhui-REGION-rhel-server" | \
        grep -v "@koji" | grep "@"
        ```
        What does it do?:
        1) yum list installed to list installed packages with source repo
        2) Pipe stderr to /dev/null because yum complains.
        3) Take out items from anaconda, because those are from OS
        4) Take out items from ansible, because we want those
        5) Take out items from rhui-REGION-rhel-server because we also want those
        6) Take out items with @koji as part of repo name because this is where packages for rhui com from
        7) Finally, only output lines with "@" in them because there are some more packages
           (ncurses, grub2, kernel-headers, other standard items) that don't have a
           repo associated with an @ symbol (shows things like 1:2.02-0.65.el7_4.2 as the repo)

- [ ] Boot existing Tower 3.3.0 AMI and run installer to perform upgrade
  - [ ] Ensure that all third party packages have been removed and replaced.
         *see command above*

