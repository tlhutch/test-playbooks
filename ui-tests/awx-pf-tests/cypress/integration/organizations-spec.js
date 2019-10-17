/**
 * Verifies basic operations on organizations.
 */
context('Organizations page', function () {
  before(function() {
    cy.createOrReplace('organizations', `del-org-${this.testID}`).as('del');
  })

  it('can delete an organization', function () {
      cy
        .visit('/#/organizations')
        .get('input[aria-label*="Search"]').type(`${this.del.name}{enter}	`)
        .get(`input[id="select-organization-${this.del.id}"][type="checkbox"]`).click()
        .get('button[aria-label="Delete"]').click()
        .get('button[aria-label="confirm delete"]').click()
        .get('.pf-c-empty-state .pf-c-empty-state__body').should('have.class', 'pf-c-empty-state__body')
  })

  it('reaches a 404 when trying to get the orgs list', function() {
    cy.server()
    cy.route({
        url: '**/api/v2/organizations/*',
        status: 404,
        response: {}
      }).as('orgs')
    cy.visit('/#/organizations')
  })

  it('can create an organization', function () {
    cy
      .visit('/#/organizations')
      .get('a[aria-label=Add]').click()
      .get('#org-name').type(`create-org-${this.testID}`)
      .get('#org-description').type(`Creation test for orgs. Test ID: ${this.testID}`)
      .get('button[aria-label=Save]').click()
      .get('dd:nth-of-type(1)').should('have.text', `create-org-${this.testID}`)
  })

  it('can edit an organization', function () {
    cy
      .get('.pf-m-primary:nth-of-type(1)').click()
      .get('#org-name').clear().type(`edited-org-${this.testID}`)
      .get('#org-description').clear().type(`Edited test for orgs. Test ID: ${this.testID}`)
      .get('button[aria-label=Save]').click()
      .get('dd:nth-of-type(1)').should('have.text', `edited-org-${this.testID}`)
  })
})
