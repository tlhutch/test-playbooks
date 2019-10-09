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

- [x] Check if a custom URL, authentication URL, username, password, and token can be configured. If a token (and optionally an auth URL) are specified, then neither username nor password can be specified, it must be either combined token/auth URL or combined username/password. 
  - [x] Check a validation error message is provided on the API response for specifying token (and optionally an auth URL) plus any of username or password.
  - [x] Check a validation error message is presented on the UI for specifying token (and optionally an auth URL) plus any of username or password.
  - [x] Check a validation error message is presented if only a username or only a password is included. (UI/API)
- [x] Check if the authentication is working for both username/password and token/auth URL.
- [x] Check if the authentication information won't be displayed on logs. Like when syncing a project and having roles/collections pulled from the primary Galaxy Server
- [x] Check that authentication information won't be shown in project update environment variables.
- [x] Check if a role/collection does not exist on the primary galaxy server it will default to the public galaxy server if (a 404 is given when querying the primary server URL).
- [x] Check that if the primary galaxy server is not available for some reason then it won't fallback to the public galaxy server, and will error.
- [x] Check if the same role/collection exists on both primary and public galaxy server if the one in the primary will be pulled/used.
- [x] Check if the PROJECT_UPDATE_VVV, PRIMARY_GALAXY_URL, PRIMARY_GALAXY_USERNAME, PRIMARY_GALAXY_PASSWORD, PRIMARY_GALAXY_AUTH_URL and PRIMARY_GALAXY_TOKEN fields are present on the UI settings page and they have some sort of value validation
~Note: Token auth support is being backported into 2.9 for automation hub, so sanity checks should be made with automation hub after merge: https://github.com/ansible/ansible/pull/63200~ -- this is complete.

## Additional Information

This work is related to the collections support being added by Ansible Tower
3.6.0 and Ansible Core 2.9. It is better to have a separated test plan to keep
things more organized.
