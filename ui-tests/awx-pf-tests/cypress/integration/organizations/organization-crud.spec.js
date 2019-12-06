/**
 * Verifies CRUD operations on organizations.
 */
context('reaches a 404 when trying to get the orgs list', function() {
  // TODO: needs to be properly implemented. Current code just demos route function
  it('reaches a 404 when trying to get the orgs list', function() {
    cy.server()
    cy.route({
      url: '**/api/v2/organizations/*',
      status: 404,
      response: {},
    }).as('orgs')
    cy.visit('/#/organizations')
    cy.get('h1[class*="pf-c-title"]').should('have.text', 'Not Found')
    cy.get('a[href="#/home"]').should('have.text', 'Back to Dashboard.')
    cy.get(`button[class=pf-c-expandable__toggle]`).click()
    cy.get('.pf-c-expandable__content strong').should('have.text', '404')
  })
})

context('Create Organization', function() {
  it('can create an organization', function() {
    cy.visit('/#/organizations')
    cy.get('a[aria-label=Add]').click()
    cy.get('#org-name').type(`create-org-${this.testID}`)
    cy.get('#org-description').type(`Creation test for orgs. Test ID: ${this.testID}`)
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `create-org-${this.testID}`)
  })
})

context('Edit Organization', function() {
  before(function() {
    cy.createOrReplace('organizations', `organization-to-edit`).as('org')
  })

  it('can edit an organization', function() {
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get(`a[href="#/organizations/${this.org.id}/edit"]`).click()
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

context('Delete Organization', function() {
  before(function() {
    cy.createOrReplace('organizations', `organization-to-delete`).as('org')
  })

  it('can delete an organization', function() {
    cy.visit('/#/organizations')
    cy.get('input[aria-label*="Search"]').type(`${this.org.name}{enter}`)
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`input[id="select-organization-${this.org.id}"][type="checkbox"]:enabled`).click()
    cy.get('button[aria-label="Delete"]:enabled').click()
    cy.get('button[aria-label="confirm delete"]:enabled').click()
    cy.get('.pf-c-empty-state .pf-c-empty-state__body').should(
      'have.class',
      'pf-c-empty-state__body'
    )
  })
})
