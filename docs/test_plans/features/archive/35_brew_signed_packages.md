# Use Brew Signed Packages

## Owner

Primary: Yanis
Secondary: Elyezer

## Summary

Starting from release 3.5.0, Ansible Tower provided RPMs should be signed with
Red Hat signing key and not Ansible, Inc signing key.


## Related Information

- [Tower Ticket](https://github.com/ansible/tower/issues/3190)
- [Red Hat Product Signing Key](https://access.redhat.com/security/team/key)


## Verification Criteria

- [ ] Install and Upgrade (Bundle and non-bundle) work as normal
- [ ] Packages retrieved are signed using Red Hat signing key


## Additional Information


### How to verify signing keys ?

```
#> rpm -q gpg-pubkey --qf 'Version: %{VERSION}\tRelease: %{RELEASE}\t%{SUMMARY}\n'
```

Will list all the package signing keys imported on your system. Look for the Red Hat key. The version is the number you are looking for.

```
#> rpm -qi ansible-tower | grep Signature
```

Will provide you with the Key ID that signed this package. Take the last 8 characters. Those 8 characters should match the version of the
key you expect it to match.
