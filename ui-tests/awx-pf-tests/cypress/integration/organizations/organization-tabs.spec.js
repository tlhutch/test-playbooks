/*
 * Tests for different tabs of an organization page.
 */
context('Add users to Organization', function() {
  beforeEach(function() {
    cy.createOrReplace('organizations', `test-org-permissions`).as('org')
    cy.createOrReplace('users', `test-org-permissions-user1`).as('user1')
    cy.createOrReplace('users', `test-org-permissions-user2`).as('user2')
  })
  it('can add users to organization', function() {
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get('dd:nth-of-type(1)').should('have.text', `${this.org.name}`)
    cy.get('button[aria-label="Access"]').click()
    cy.get('button[aria-label="Add"]').click()
    cy.get('[data-cy="add-role-users"]').click()
    cy.get('footer button[type="submit"]').click()
    cy.get('[class="pf-c-wizard__inner-wrap"] [aria-label="Search text input"]').type(
      `${this.user1.username}{enter}`
    )
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`[name="${this.user1.username}"][type="checkbox"]`).click()
    cy.get('.searchTagChip button[aria-label="close"]').click()
    cy.get('[class="pf-c-wizard__inner-wrap"] [aria-label="Search text input"]').type(
      `${this.user2.username}{enter}`
    )
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`[name="${this.user2.username}"][type="checkbox"]`).click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
    cy.get('[aria-label="Admin"][type="checkbox"]').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
    cy.get(`[href="#/users/${this.user1.id}/details"]`).should(
      'have.text',
      `${this.user1.username}`
    )
    cy.get(`[href="#/users/${this.user2.id}/details"]`).should(
      'have.text',
      `${this.user2.username}`
    )
  })

  it.skip('reaches a 404 when trying to get the users list', function() {
    // TODO: Improve this test
    cy.server()
    cy.route({
      url: '**/api/v2/users/*',
      status: 404,
      response: {},
    }).as('orgs')
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get('button[aria-label="Access"]').click()
    cy.get('button[aria-label="Add"]').click()
    cy.get('[data-cy="add-role-users"]').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
  })
})

context('Add teams to Organization', function() {
  beforeEach(function() {
    cy.createOrReplace('organizations', `test-org-permissions`).as('org')
    cy.createOrReplace('teams', `test-org-permissions-team1`).as('team1')
    cy.createOrReplace('teams', `test-org-permissions-team2`).as('team2')
  })
  it('can add teams to organization', function() {
    // Issue: This is not working ATM
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get('dd:nth-of-type(1)').should('have.text', `${this.org.name}`)
    cy.get('button[aria-label="Access"]').click()
    cy.get('button[aria-label="Add"]').click()
    cy.get('[data-cy="add-role-teams"]').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
    cy.get('[class="pf-c-wizard__inner-wrap"] [aria-label="Search text input"]').type(
      `${this.team1.name}{enter}`
    )
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`[name="${this.team1.name}"][type="checkbox"]`).click()
    cy.get('.searchTagChip button[aria-label="close"]').click()
    cy.get('[class="pf-c-wizard__inner-wrap"] [aria-label="Search text input"]').type(
      `${this.team2.name}{enter}`
    )
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get(`[name="${this.team2.name}"][type="checkbox"]`).click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
    cy.get('[aria-label="Admin"][type="checkbox"]').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
  })

  it.skip('reaches a 404 when trying to get the teams list', function() {
    // TODO: Improve this test
    cy.server()
    cy.route({
      url: '**/api/v2/teams/*',
      status: 404,
      response: {},
    }).as('orgs')
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get('button[aria-label="Access"]').click()
    cy.get('button[aria-label="Add"]').click()
    cy.get('[data-cy="add-role-teams"]').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
  })
})
