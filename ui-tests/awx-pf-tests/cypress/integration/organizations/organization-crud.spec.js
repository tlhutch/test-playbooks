/**
 * Verifies CRUD operations on organizations.
 */
context('Organization CRUD operations', function() {
  // Aliases used in setup must be done with beforeEach(), not before()
  // Aliases are wiped between tests for isolation
  beforeEach(function() {
    cy.createOrReplace('organizations', `test-organization`).as('org')
  })

  // TODO: needs to be properly implemented. Current code just demos route function
  it('reaches a 404 when trying to get the orgs list', function() {
    cy.server()
    cy.route({
      url: '**/api/v2/organizations/*',
      status: 404,
      response: {},
    }).as('orgs')
    cy.visit('/#/organizations')
  })

  it('can create an organization', function() {
    cy.visit('/#/organizations')
    cy.get('a[aria-label=Add]').click()
    cy.get('#org-name').type(`create-org-${this.testID}`)
    cy.get('#org-description').type(`Creation test for orgs. Test ID: ${this.testID}`)
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `create-org-${this.testID}`)
  })

  it('can delete an organization', function() {
    // Searchbars aren't implemented yet
    this.skip()
  })

  it('can edit an organization', function() {
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get('.pf-m-primary:nth-of-type(1)').click()
    cy.get('#org-name')
      .clear()
      .type(`edited-org-${this.testID}`)
    cy.get('#org-description')
      .clear()
      .type(`Edited test for orgs. Test ID: ${this.testID}`)
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `edited-org-${this.testID}`)
  })
})
