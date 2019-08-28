# Primary Galaxy Server

## Owners

API: Elyézer (@elyezer), Mat (@one-t)

UI: Danny (@dsesami), Caleb (@squidboylan)

## Summary

Allow users to configure a primary Ansible Galaxy server by providing a custom
URL and authentication information. This will still set up the public galaxy
server as a fallback.

## Related Information

- [AWX PR](https://github.com/ansible/awx/pull/4589)
- [Initial API tests PR](https://github.com/ansible/tower-qa/pull/4005)
- [tower-qa Ticket](https://github.com/ansible/tower-qa/issues/4018)

## Verification Criteria

- [ ] Check if a custom URL, username, password and token can be configured. If token is specified then neither username nor password can be specified, it must be either token or username/password.
  - [ ] Check a validation error message is provided on the API response for specifying token plus any of username or password.
  - [ ] Check a validation error message is presented on the UI for specifying token plus any of username or password.
- [ ] Check if the authentication is working for both username/password and token.
- [ ] Check if the authentication information won't be displayed on logs. Like when syncing a project and having roles/collections pulled from the primary Galaxy Server
- [ ] Check if a role/collection does not exist on the primary galaxy server it will default to the public galaxy server. This will only happen if a 404 is given when querying the primary server URL. If the primary galaxy server is not available for some reason then it won't fallback to the public galaxy server.
- [ ] Check if the same role/collection exists on both primary and public galaxy server if the one in the primary will be pulled/used.
- [ ] Check if the PROJECT_UPDATE_VVV, PRIMARY_GALAXY_URL, PRIMARY_GALAXY_USERNAME, PRIMARY_GALAXY_PASSWORD and PRIMARY_GALAXY_TOKEN fields are present on the UI settings page and they have some sort of value validation

## Additional Information

This work is related to the collections support being added by Ansible Tower
3.6.0 and Ansible Core 2.9. It is better to have a separated test plan to keep
things more organized.
