/**
 * Generates a random number to be assigned to each individual test run.
 * This is useful for randomly generated names for resources used in tests.
 */
Cypress.Commands.add('generateTestID', () => cy.wrap(`${Cypress._.random(0, 1e10)}`).as('testID'));

/**
 * Shell built around cy.request(). Cypress attempts to handle CSRF token verification to an extent,
 * but AWX uses headers that Cypress doesn't handle out of the box. This utility function allows
 * cy.request() to interact with the AWX server correctly.
 *
 * @param {string} method - REST call. Can be GET, POST, PUT, DELETE...
 * @param {string} url - API endpoint to access. Base URL is configured,
 *                       so you may type '/api/v2/organizations', for example.
 * @param {Object} body - Body of the request made.
 * @param {boolean} form - False by default. This is set to true for login functions, mostly,
 *                         but its behavior can be viewed in the documentation for cy.request().
 */
Cypress.Commands.add('apiRequest', (method, url, body, form = false) => {
  cy.request(url).then(() => cy.getCookie('csrftoken').then((cookie) => {
    body.csrfmiddlewaretoken = cookie.value
    cy.request({
      method,
      url,
      form,
      headers: {
        'referer': `${Cypress.config().baseUrl}/api/login/`,
        'x-csrftoken': `${cookie.value}`
      },
      body: body
    })
  }));
});

/**
 * Logs into the AWX server. CSRF tokens are cleared on every test in Cypress for complete
 * test isolation. As such, this is called in the beforeEach() function of all tests
 * (see cypress/support/index.js).
 * */
Cypress.Commands.add('login', () => {
  const body = {
    username: Cypress.env('AWX_E2E_USERNAME'),
    password: Cypress.env('AWX_E2E_PASSWORD'),
    next: '/api/'
  };
  cy.apiRequest('POST', `/api/login/`, body, true);
});

/**
 * Performs a POST to the AWX API to create a new organization.
 * TODO: Refactor creation functions to perform a getOrCreate() function
 * that supports various resources.
 *
 * @param {string} name
 * @param {string} description
 * @return {string} id - The ID of the created organization.
 * */
Cypress.Commands.add('createOrg', (name, description) => {
  const body = {
    name: `${name}`,
    description: `${description}`
  };
  cy.apiRequest('POST', '/api/v2/organizations/', body)
    .then((response) => response.body.id);
});
