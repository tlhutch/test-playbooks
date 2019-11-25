/*
 * Tests to ensure that the application is functioning at a basic level.
 * This suite should have read-only tests. When adding tests to this file,
 * avoiding actually creating/deleting/editing resources.
 */
context('Sanity checks', function() {
  it('Can log out and log in', function() {
    // Every test is preceded by an API login, so for this one we log out first.
    cy.visit('')
    cy.get('#toolbar-user-dropdown').click()
    cy.get('#logout-button').click()
    cy.get('.pf-c-login__container').should('be.visible')

    cy.get('#pf-login-username-id').type(Cypress.env('AWX_E2E_USERNAME'))
    cy.get('#pf-login-password-id').type(Cypress.env('AWX_E2E_PASSWORD'))
    cy.get('button[type=submit]').click()
    cy.get('#page-sidebar').should('be.visible')
  })

  it.skip('Can view the dashboard components', function() {
    cy.visit('')
  })

  it.skip('Can view each page with basic user privileges', function() {})
  it('Can view each page with administrative privileges', function() {
    // Navigation bar check
    cy.visit('')

    // Expand all Navbar groups
    cy.get('[data-component="pf-nav-expandable"][aria-expanded="false"]')
      .each(function(item) {
        cy.wrap(item).click()
      })
      .then(function() {
        // Verify that each navbar item links to the correct page
        const navItem = '.pf-c-nav__item'
        const header = '.pf-c-breadcrumb__heading'

        cy.get(`${navItem} > [href="/#/jobs"]`).click()
        cy.get(header).should('have.text', 'Jobs')

        cy.get(`${navItem} > [href="/#/organizations"]`).click()
        cy.get(header).should('have.text', 'Organizations')

        // TODO: Other pages
      })
  })
  it.skip('Can view each page with auditor privileges', function() {})
  it.skip('Can click-away on pop-ups', function() {})
  it.skip('Has an :actionable save button on form change', function() {})
  it.skip('Does not have an actionable save button without form changes', function() {})
})
