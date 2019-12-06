/**
 * Verifies CRUD operations on Teams.
 */
context('Reaches a 404', function() {
  it('reaches a 404 when trying to get the teams list', function() {
    cy.server()
    cy.route({
      url: '**/api/v2/teams/*',
      status: 404,
      response: {},
    }).as('teams')
    cy.visit('/#/teams')
    cy.get('h1[class*="pf-c-title"]').should('have.text', 'Not Found')
    cy.get('a[href="#/home"]').should('have.text', 'Back to Dashboard.')
    cy.get(`button[class=pf-c-expandable__toggle]`).click()
    cy.get('.pf-c-expandable__content strong').should('have.text', '404')
  })
})
context('Create a team', function() {
  before(function() {
    cy.createOrReplace('organizations', `organization-for-team`).as('org')
  })
  it('can create a team', function() {
    cy.visit('/#/teams')
    cy.get('a[aria-label=Add]').click()
    cy.get('#team-name').type(`create-team-${this.testID}`)
    cy.get('#team-description').type(`Creation test for Teams. Test ID: ${this.testID}`)
    cy.get('#organization').click()
    cy.get('input[aria-label*="Search text input"]').type(`${this.org.name}{enter}`)
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`#selected-${this.org.id}`).click()
    cy.get('[aria-label="Select Organization"] button[class*="pf-m-primary"]').click()
    cy.get('button[aria-label=Save]').click()
    cy.get('dd[data-cy*="name"]').should('have.text', `create-team-${this.testID}`)
  })
})

context('Edit a team', function() {
  before(function() {
    cy.createOrReplace('teams', `team-to-edit`).as('team')
  })

  it('can edit a team', function() {
    cy.visit(`/#/teams/${this.team.id}`)
    cy.get('a[href*="edit"]').click()
    cy.get('#team-name')
      .clear()
      .type(`edit-team-${this.testID}`)
    cy.get('#team-description')
      .clear()
      .type(`Edited test for Teams. Test ID: ${this.testID}`)
    cy.get('button[aria-label=Save]').click()
    cy.get('dd[data-cy*="name"]').should('have.text', `edit-team-${this.testID}`)
  })
})

context('Delete a team', function() {
  before(function() {
    cy.createOrReplace('teams', `team-to-delete`).as('del')
  })
  it('can delete a team', function() {
    cy.visit('/#/teams')
    cy.get('input[aria-label*="Search"]').type(`${this.del.name}{enter}`)
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`input[id="select-team-${this.del.id}"][type="checkbox"]:enabled`).click()
    cy.get('button[aria-label="Delete"]:enabled').click()
    cy.get('button[aria-label="confirm delete"]:enabled').click()
    cy.get('.pf-c-empty-state .pf-c-empty-state__body').should(
      'have.class',
      'pf-c-empty-state__body'
    )
  })
})
