/*
 * Tests for Job-Template-specific operations outside of basic CRUD operations.
 */
context('Launch a Job Template without prompts', function() {
  before(function() {
    cy.createOrReplace('job_templates', `JT-to-launch`).as('launch')
  })

  it('can launch job template without prompts', function() {
    this.skip() // only till the nth-of-child element is replaced with a proper selector
    cy.visit('/#/templates')
    cy.get('input[aria-label*="Search"]').type(`${this.launch.name}{enter}`)
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get('[aria-label="Templates List"] .pf-c-data-list__item-row button').click()
    cy.get('dd:nth-child(2)').should('have.text', 'Running')
    // Issue: the job status does not change to successful unless page is refreshed
    // .get('dd:nth-child(2)').should('have.text', 'Successful')
  })
})

context.skip('Launch a Job Template with prompts', function() {
  before(function() {
    cy.createOrReplace('job_templates', `JT-to-launch`).as('launch')
  })
  it('can launch job template with prompts', function() {
    this.skip() // prompts not implemented yet
    cy.visit('/#/templates')
    cy.get('input[aria-label*="Search"]').type(`${this.launch.name}{enter}`)
    cy.get('[class*=FilterTags__ResultCount-sc-4lbi43-1]').should('have.text', '1 results')
    cy.get('[aria-label="Templates List"] .pf-c-data-list__item-row button').click()
    cy.get('dd:nth-child(2)').should('have.text', 'Running')
    cy.get('dd:nth-child(2)').should('have.text', 'Successful')
  })
})
