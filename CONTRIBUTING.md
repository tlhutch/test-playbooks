# Tower-QA

Hello! Excited to have you join us.

If you have any questions about this document, reach out to the team on the `ship_it` channel in slack.
If you have any updates, make a PR!

## Branching strategy
## Feature Test Branches

When working on a feature with a developer, create a branch based off of master
for the feature. For this example, we will call our feature, `feature-123`. Say
there are two testers and one developer working on this feature, named:
* `cow`
* `moose`
* `ant`

Then they would each create branches named
* `cow-feature-123`
* `moose-feature-123`
* `and-feature-123`.

As they write tests, they make PRs against `feature-123`. This allows them to
move fast and get reviews on small changes, and it makes it clear what the new
changes are that need reviewed instead of having one branch they all hammer
against and where the PR history grows as the branch may live for the entire
duration of the sprint, or even longer if it is a larger feature.

You may like to intermittently rebase `feature-123` off of master and then your
personal branch `cow-feature-123` off of `feature-123` to keep up with changes
in master.

When the feature is complete, then the tester can make the final PR of
`feature-123` against master. If any commit squashing needs to happen to make a
sensible history, this can be done at this time.

## Release Branches
#TODO: Update this section
