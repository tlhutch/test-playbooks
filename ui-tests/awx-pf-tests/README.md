## AWX-PF E2E
### Introduction
This is an automated functional test suite for the AWX Patternfly UI. It uses Cypress as its base framework.

*See CONTRIBUTING.md for guidelines on what to do before opening a PR.*

### Framework Reference 
- [Cypress Github page](https://github.com/cypress-io/cypress)
- [Cypress Docs](https://docs.cypress.io)
- [Percy Docs](https://docs.percy.io/docs/cypress)
- [awxkit](https://github.com/ansible/awx/tree/devel/awxkit)

### Requirements and Installation

Details for setting up the UI itself are located [here](https://github.com/ansible/awx/tree/devel/awx/ui_next). The tests require the UI to be up and running.

### Quick Setup
There is a script provided for convenience that will set up the python and node environment for you in advance. It will store the environment in `${HOME}/.pf` by default, but you can change `$PF_VIRTUALENV_DIR` within the script to whatever directory you like.

This block only needs to be run whenever you want to update awxkit or Cypress. This shouldn't need to be done that often.
```
# Run setup script for Python/Node shared virtual environment
./setup_virtual_environment.sh

# Turn on virtual environment that has been created
source ~/.pf/pf-virtualenv/bin/activate

# Set variables to access AWX
export CYPRESS_AWX_E2E_USERNAME=username
export CYPRESS_AWX_E2E_PASSWORD=password
export CYPRESS_baseUrl=https://localhost:3001 # No trailing slash!

npm run cypress # or npm run cypress-headless

```

`npm run cypress` turns on the Cypress GUI, where you can launch and watch individual tests in action. `npm run cypress-headless` just runs all the tests in the terminal. 

Subsequent runs just need this:
```
# Turn your environment on; recommend making this an alias so it's easier to type
source ~/.pf/pf-virtualenv/bin/activate

# Make sure your environment variables for username, password,
# and target URL are set somewhere as above

npm run cypress-headless
```

You can exit your virtual environment by running `deactivate`.

### Manual Setup:
Follow these instructions if you have problems with the setup script.

Since this suite leverages `awxkit` to perform setup functions, you'll need to have a Python 3 virtual environment that has `awxkit` installed, as well as `nodeenv` so that the Node and Python virtual environments are shared.
```
# Set up virtual environment
python3 -m venv ~/some_directory

# Activate virtual environment
source ~/some_directory/bin/activate # Activate virtual environment

# Install awxkit for use in fixtures:
git clone https://github.com/ansible/awx
pip install -e awx/awxkit[crypto] -r awx/awxkit/requirements.txt

```

Now, link a Node virtual environment to the Python virtual environment:
```
# While Python virtual environment is active
pip install nodeenv

# Tell nodeenv to use the Python virtualenv with the -p flag
nodeenv -p

# Install dependencies within tower-qa/ui-tests/awx-pf-tests
npm install
```

You should now have a functional virtual environment. 

In `cypress.json`, set the baseUrl value to that of the target UI you are testing. Do NOT include a trailing slash. This will break `awxkit` functions. For example, "https://localhost:3001" is fine, but "https://localhost:3001/" is not. You can also set this as an environment variable, as in the example below. 

Cypress can _only_ see environment variables with the `CYPRESS_` prefix, or variables set in a Cypress config file. `CYPRESS_FOO` is available within the tests as `FOO`.

```
# Set variables to access AWX
export CYPRESS_AWX_E2E_USERNAME=username
export CYPRESS_AWX_E2E_PASSWORD=password
export CYPRESS_baseUrl=https://localhost:3001 # No trailing slash!

```

Further reading on how Cypress consumes environment variables is located [here](https://docs.cypress.io/guides/guides/environment-variables.html#Setting). 


To open the Cypress test inspection tools to assist with test development (assumes you are at the top level directory of `tower-qa`):
```
npm --prefix tower-qa/ui-tests-/awx-pf-tests run cypress
```

To run the test suite in headless mode (assuming you are in the same directory as `cypress.json`):
```
npm run cypress-headless
```

### Integrating Percy with your Cypress tests:

Before you can successfully run Percy, the PERCY_TOKEN environment variable must be set.
The token can be found in your project settings on percy dashboard

```
export PERCY_TOKEN=<your token here>
```
Now, insert the cypress command `cy.percySnapshot()` in the tests where you would like percy to take snapshots for visual diffing.

For more options to adjust attributes like snapshot name, width and height, follow the documentation [here](https://docs.percy.io/docs/cypress#section-configuration)

Finally, use the following command to run the tests:
```
percy exec -- cypress run
```

That's it! Now, whenever CI runs, a snapshot of the app in that state will be uploaded to Percy for visual regression testing!


### Directory Organization
At the top level, there is a `cypress.json` file and a `cypress/` directory; within this directory, there are four folders:
- `fixtures/`: Contains JSON payloads for usage in tests.
- `integration/`: Contains the tests themselves.
- `plugins/`: Contains the loader for Cypress plugins and any plugins you might like to add.
- `support/`: Contains custom commands and setup functions for global use in the test suite.

#### Key Tests
- `sanity.spec.js`: Contains a sanity check test suite. It is read-only and does not create any resources, and only makes sure the basic UI is functional.
- `akit.spec.js`: Contains tests that make API calls with `awxkit`. If this does not pass, there is a configuration problem, or you have not activated your virtual environment.

For more information regarding these folders and files, please see the Cypress documentation.

### Tips and Tricks
- `support/commands.js` contains plenty of helper functions. Of note are `akit` and `createOrReplace`, the first of which calls `akit_client.py` to authenticate with `akit` and perform any awxkit v2 command you'd like. For example, calling `cy.akit('job_templates.create()')` in Cypress is the same thing as going to awxkit directly and calling `v2.job_templates.create()`. 

- `cy.createOrReplace('job_templates', 'something')` is just a shortcut function to avoid having to write `cy.akit('job_templates.create_or_replace("name=something")')`. In case you don't know, v2.xyz.create_or_replace requires a `username` param instead of `name` when creating users, but the wrapper function handles that for you.
- When calling commands directly with `cy.akit()`, make sure you look at how the command is accepted in awxkit to ensure correct syntax. 
- If you need a for-loop that can iterate over a list of elements, you can't do a traditional loop, unfortunately. This is because of the async nature of Cypress and the way event ordering is handled. You can generate an array, then use that array within the same test context to iterate over numbered elements. An example:
    ```
    // Generate an array of the numbers 1-5
    let arr = Array.from({length:5}, (v, k) => k + 1)

    // cy.wrap the array, which will keep the event order straight 
    cy.wrap(arr).each(function(i) {
      cy.createOrReplace('credentials', `test-credentials-${i}`).as(`cred${i}`)
    })

    ```
  This will then generate five credential objects, named `test-credentials-1`, and so forth. The .as(`cred${i}`) section will make each object available as `this.creds1`, `this.creds2`, and so on.

- Cypress clears UI session data entirely during each test to avoid caching and cookie issues. Sometimes, this means you need to manipulate cookies directly yourself. For an example, see the custom `apiRequest()` function present in `cypress/support/commands.js`.

- Avoid overlapping dependencies as much as possible. You have two options. The current configuration calls a custom command, `generateTestID()`, which is has been made available as `this.testID` in every individual test. Feel free to use this to generate custom name suffixes to avoid conflicts. `cy.createOrReplace()` uses awxkit's `create_or_replace()` function, which will replace an existing item and keep it fresh every run. See `cypress/integration/akit.spec.js` for examples.


### Docker
```
cd tower-qa/ui-tests/awx-pf-tests
docker build -t awx-pf-tests .
docker run --network tools_default --link 'tools_ui_next_1:ui-next' -v $PWD:/e2e -w /e2e awx-pf-tests run --project .
```
