##### ISSUE TYPE
 - Test cases for https://github.com/ansible/awx/pull/2351

##### COMPONENT NAME
 - UI

##### SUMMARY
Two new views:
First, the permissions modal on the Teams page now has an “organizations” tab to build resource permissions.
![screen shot 2018-10-04 at 1 14 53 pm](https://user-images.githubusercontent.com/19942822/47034557-b5551200-d145-11e8-8950-686c4148bfbe.png)

Second, the modal for adding permissions to organizations has a teams tab where you can mass-assign permissions to all users on a particular team.
![screen shot 2018-10-04 at 1 17 13 pm](https://user-images.githubusercontent.com/19942822/47034564-bdad4d00-d145-11e8-8db1-f7b900d13540.png)

## Test Cases
- [ ] Ensure permissions can be added and edited properly on the Organizations tab in the Teams page "Permissions" modal. Ensure that those permissions work for roles both assigned to individual users and users that are members of teams.

The modal for adding permissions to organizations has a teams tab where you can mass-assign permissions to all users on a particular team:
- [ ] Ensure that all UI elements in this tab function properly.
- [ ] Ensure that mass-assignment works properly for users on a certain team.
- [ ] On the organizations permissions pane, double-check the addition / removal of multiple roles at a time.
- [ ] Verify My Activity View shows permission-related activity from the new views.
