# Credential Plugins

## Feature Summary

This feature introduces the ability to retrieve credentials from an external secrets management product.

This will involve creating a credential to access the secret manager, and defining the location from which to obtain the secret in another credential

## Related Information

* [AWX Ticket](https://github.com/ansible/awx/issues/2238)

## Prerequisites

* [ ] Infrastructure
  * [ ] CyberArk
  * [ ] HashiCorp Vault
  * [ ] Azure Keyvault

## Acceptance criteria

* [ ] API
  * [ ] Secrets can be retrieved from
    * [ ] CyberArk
    * [ ] HashiCorp Vault
    * [ ] Azure Keyvault
  * [ ] Failure to retrieve secrets results in a descriptive error
  * [ ] SSH Keys retrieved from Secrets Manager can be used for authentication
  * [ ] Vault Passwords retrieved from Secrets Manager can decrypt a vault
  * [ ] All Credential Types can be retrieved from a Secrets Manager
  * [ ] Existing Secrets can be converted to remote secrets and back
  * [ ] Secret Manager secrets can be used in a custom credential type
  * [ ] RBAC
    * [ ] A user granted access to a credential that uses the SM credential can use it in a job template without access to the SM credential ??
    * [ ] A user with admin access on a credential cannot change it if they don't have access to the SM credential
