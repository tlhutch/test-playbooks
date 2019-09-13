## AWX-PF E2E
#### Introduction
This is an automated functional test suite for the AWX Patternfly UI. It uses Cypress as its base framework.

#### Framework Reference 
- [Cypress Github page](https://github.com/cypress-io/cypress)
- [Cypress Docs](https://docs.cypress.io)

#### Requirements and installation.
See details for awx-pf setup in general [here](https://github.com/ansible/awx/tree/devel/awx/ui_next). Installation steps for awx-pf installs the dependencies needed to run Cypress. If you're not spinning up the awx-pf instance yourself, use the nodeJS and npm requirements listed in the aforementioned UI repo link, and then ensure Cypress is installed via npm:
```
npm install cypress  # --save-dev option will update dependencies in package.json
```

npm's default installation also includes `npx`, which allows you to execute npm modules directly without searching for the binary executable path. If you don't have this dependency, install it via npm:
```
npm install -g npx
```

#### Configuration
In `cypress.json`, set the baseUrl value to that of the target UI you are testing. Inserting your credentials into cypress.json in plaintext isn't recommended, for standard security resasons. There are multiple ways to override the variables, listed [here](https://docs.cypress.io/guides/guides/environment-variables.html#Setting). The simplest way is to take an environment variable and prefix it with `CYPRESS_`. Cypress searches for this environment variable prefix and
makes it available. For example, to override `AWX_E2E_USERNAME`:
```
CYPRESS_AWX_E2E_USERNAME=foo npx cypress open # etc, etc,
```

#### Usage
To run the test suite in headless mode (assuming you are in the same directory as `cypress.json`):
```
npx cypress run
```
*NOTE:* The `--project` option needs to be added and pointed to the directory containing `cypress.json` if this command isn't executed in the same directory. Depending on configuration, if it does not find an existing project, Cypress will then otherwise generate an example `cypress.json` and `cypress/` directory with a demo test suite. For example:
```
npx cypress run --project awx/something/directory-containing-cypress-json
```

To open the Cypress test inspection tools to assist with test development:
```
npx cypress open  # uses --project option the same way as `cypress run`
```

#### Directory Organization
At the top level, there is a `cypress.json` file and a `cypress/` directory; within this directory, there are four folders:
- `fixtures/`: Contains JSON payloads for usage in tests.
- `integration/`: Contains the tests themselves.
- `plugins/`: Contains the loader for Cypress plugins and any plugins you might like to add.
- `support/`: Contains custom commands and setup functions for global use in the test suite.

For more information regarding these folders, please see the Cypress documentation.

#### Tips and Tricks
- Cypress clears UI session data entirely during each test to avoid caching and cookie issues. Sometimes, this means you need to manipulate cookies directly yourself. For an example, see the custom `apiRequest()` function present in `cypress/support/commands.js`.
- Avoid overlapping dependencies as much as possible. The current configuration calls a custom command, `generateTestID()`, which is has been made available as `this.testID` in every individual test. Feel free to use this to generate custom name suffixes to avoid conflicts.
- When setting up a UI test, any previous setup should be done through the API first. Making this more robust (potentially using AWX's CLI or awxkit) is future work at time of writing.
