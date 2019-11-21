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
    cy.get('div.pf-c-wizard__outer-wrap > div >main > div > div > div:nth-child(2)').click()
    cy.get('[class="pf-c-wizard__inner-wrap"] [aria-label="Search text input"]').type(
      `${this.user1.username}{enter}	`
    )
    cy.get(`[name="${this.user1.username}"][type="checkbox"]`).click()
    cy.get('[aria-label="Clear all search filters"]').click()
    cy.get('[class="pf-c-wizard__inner-wrap"] [aria-label="Search text input"]').type(
      `${this.user2.username}{enter}	`
    )
    cy.get(`[name="${this.user2.username}"][type="checkbox"]`).click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
    cy.get('[aria-label="Admin"][type="checkbox"]').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
    cy.get(`[href="#/api/v2/users/${this.user1.id}/"]`).should(
      'have.text',
      `${this.user1.username}`
    )
    cy.get(`[href="#/api/v2/users/${this.user2.id}/"]`).should(
      'have.text',
      `${this.user2.username}`
    )
  })

  it('reaches a 404 when trying to get the users list', function() {
    // Issue: does not throw the 404 error
    cy.server()
    cy.route({
      url: '**/api/v2/users/*',
      status: 404,
      response: {},
    }).as('orgs')
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get('button[aria-label="Access"]').click()
    cy.get('button[aria-label="Add"]').click()
    cy.get('div.pf-c-wizard__outer-wrap > div >main > div > div > div:nth-child(2)').click()
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
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get('dd:nth-of-type(1)').should('have.text', `${this.org.name}`)
    cy.get('button[aria-label="Access"]').click()
    cy.get('button[aria-label="Add"]').click()
    cy.get('div.pf-c-wizard__outer-wrap > div >main > div > div > div:nth-child(3)').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
    cy.get('[class="pf-c-wizard__inner-wrap"] [aria-label="Search text input"]').type(
      `${this.team1.name}{enter}	`
    )
    cy.get(`[name="${this.team1.name}"][type="checkbox"]`).click()
    cy.get('[aria-label="Clear all search filters"]').click()
    cy.get('[class="pf-c-wizard__inner-wrap"] [aria-label="Search text input"]').type(
      `${this.team2.name}{enter}	`
    )
    cy.get(`[name="${this.team2.name}"][type="checkbox"]`).click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
    cy.get('[aria-label="Admin"][type="checkbox"]').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
  })

  it('reaches a 404 when trying to get the teams list', function() {
    // Issue: does not throw the 404 error
    cy.server()
    cy.route({
      url: '**/api/v2/teams/*',
      status: 404,
      response: {},
    }).as('orgs')
    cy.visit(`/#/organizations/${this.org.id}`)
    cy.get('button[aria-label="Access"]').click()
    cy.get('button[aria-label="Add"]').click()
    cy.get('div.pf-c-wizard__outer-wrap > div >main > div > div > div:nth-child(3)').click()
    cy.get('[class="pf-c-wizard__footer"] [class="pf-c-button pf-m-primary"]').click()
  })
})
