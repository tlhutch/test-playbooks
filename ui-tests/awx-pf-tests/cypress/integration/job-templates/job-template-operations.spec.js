/*
 * Tests for Job-Template-specific operations outside of basic CRUD operations.
 */
context('Launch a Job Template without prompts', function() {
  before(function() {
    cy.createOrReplace('job_templates', `JT-to-launch`).as('launch')
  })

  it('can launch job template without prompts', function() {
    cy.visit('/#/templates')
    cy.get('input[aria-label*="Search"]').type(`${this.launch.name}{enter}	`)
    cy.wait(1000)
    cy.get('[aria-label="Templates List"] .pf-c-data-list__item-row button').click()
    cy.get('dd:nth-child(2)').should('have.text', 'Running')
    // Issue: the job status does not change to successful unless page is refreshed
    // .get('dd:nth-child(2)').should('have.text', 'Successful')
  })
})

context.skip('Launch a Job Template without prompts', function() {
  before(function() {
    cy.createOrReplace('job_templates', `JT-to-launch`).as('launch')
  })
  it('can launch job template with prompts', function() {
    this.skip() // prompts not implemented yet
    cy.visit('/#/templates')
    cy.get('input[aria-label*="Search"]').type(`${this.launch.name}{enter}	`)
    cy.wait(500)
    cy.get('[aria-label="Templates List"] .pf-c-data-list__item-row button').click()
    cy.get('dd:nth-child(2)').should('have.text', 'Running')
    cy.wait(5000)
    cy.get('dd:nth-child(2)').should('have.text', 'Successful')
  })
})
