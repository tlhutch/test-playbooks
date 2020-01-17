# Contributing

Before making commits, ensure that `eslint` likes your code, and use `prettier` to automatically format it.

Make a commit and save your work before running these, then squash commits afterwards.

- `npm run prettier-check`: See what files will be changed before you run `prettier`.
- `npm run prettier`: This will clean your files up for you, but be careful with it! Run `git diff` afterwards for a sanity check.
- `npm run lint`: Fix any errors or warnings you see. After running `prettier`, there probably isn't anything, but it's good to make sure.

- It is recommended to run `prettier-check` once more after this. 

- Finally, run `npm run cypress-headless` and make sure the tests are stable.

After this is done, feel free to open a PR (don't commit `cypress.json` unless you are making configuration changes!)
