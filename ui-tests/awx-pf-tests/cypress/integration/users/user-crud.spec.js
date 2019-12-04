/**
 * Verifies CRUD operations on Users.
 */
context('Reaches a 404', function() {
  it('reaches a 404 when trying to get the Users list', function() {
    cy.server()
    cy.route({
      url: '**/api/v2/users/*',
      status: 404,
      response: {},
    }).as('user')
    cy.visit('/#/users')
    cy.get('h1[class*="pf-c-title"]').should('have.text', 'Not Found')
    cy.get('a[href="#/home"]').should('have.text', 'Back to Dashboard.')
    cy.get(`button[class=pf-c-expandable__toggle]`).click()
    cy.get('.pf-c-expandable__content strong').should('have.text', '404')
  })
})
context('Create a User', function() {
  before(function() {
    cy.createOrReplace('organizations', `organization-for-team`).as('org')
  })
  it('can create a user', function() {
    cy.visit('/#/users')
    cy.get('a[aria-label=Add]').click()
    cy.get('#user-username').type(`create-user-${this.testID}`)
    cy.get('#user-email').type(`${this.testID}@example.com`)
    cy.get('#user-password').type(`${this.testID}`)
    cy.get('#user-confirm-password').type(`${this.testID}`)
    cy.get('#user-first-name').type(`user-${this.testID}`)
    cy.get('#user-last-name').type(`user-${this.testID}`)
    cy.get('#organization').click()
    cy.get('input[aria-label*="Search text input"]').type(`${this.org.name}{enter}`)
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`#selected-${this.org.id}`).click()
    cy.get('[aria-label="Select Organization"] button[class*="pf-m-primary"]').click()
    cy.get('#user-type').select('System Auditor')
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `create-user-${this.testID}`)
  })
})

context('Edit a User', function() {
  before(function() {
    cy.createOrReplace('users', `user-to-edit`).as('user')
  })

  it('can edit a user', function() {
    cy.visit(`/#/users/${this.user.id}`)
    cy.get('a[aria-label=edit]').click()
    cy.get('#user-username')
      .clear()
      .type(`edited-user-${this.testID}`)
    cy.get('#user-email')
      .clear()
      .type(`${this.testID}@example.com`)
    cy.get('#user-password')
      .clear()
      .type(`${this.testID}`)
    cy.get('#user-confirm-password')
      .clear()
      .type(`${this.testID}`)
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `edited-user-${this.testID}`)
  })
})

context('Delete a User', function() {
  before(function() {
    cy.createOrReplace('users', `user-to-delete`).as('del')
  })
  it('can delete a user', function() {
    cy.visit('/#/users')
    cy.get('input[aria-label*="Search"]').type(`${this.del.username}{enter}`)
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`input[id="select-user-${this.del.id}"][type="checkbox"]`).click()
    cy.get('button[aria-label="Delete"]:enabled').click()
    cy.get('button[aria-label="confirm delete"]:enabled').click()
    cy.get('.pf-c-empty-state .pf-c-empty-state__body').should(
      'have.class',
      'pf-c-empty-state__body'
    )
  })
})
