### How to Test RADIUS Authentication

Install an environment with:
```
ansible-playbook playbooks/deploy-tower-radius.yml -i playbooks/inventory -e @playbooks/images-radius.yml -e @playbooks/vars.yml
```
* `vars.yml` is just an example file containing extra variables, see the getting started guide.

On the Tower server:
* Install an enterprise license.
* PATCH the following to `/api/v2/settings/radius/`:
```
{
    "RADIUS_SERVER": "ec2-fake.compute-1.amazonaws.com",
    "RADIUS_PORT": 1812,
    "RADIUS_SECRET": "testing123"
}
```

Authenticate to Tower with a user defined in the RADIUS server:
* RADIUS user username is `radius_user`.
* Password is [here](https://github.com/ansible/tower-qa/blob/master/playbooks/roles/freeradius/vars/main.yml#L2).

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) August 8th, 2018.
