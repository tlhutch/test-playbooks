/*
 * Tests for Job-Template-specific operations outside of basic CRUD operations.
 Since the Page is changing very often, skipping the tests for now
 */
context.skip('Launch a Job Template without prompts', function() {
  before(function() {
    cy.createOrReplace('job_templates', `JT-to-launch`).as('launch')
  })

  it('can launch job template without prompts', function() {
    cy.visit('/#/templates')
    cy.get('input[aria-label*="Search"]').type(`${this.launch.name}{enter}`)
    cy.get('[aria-label="Templates List"]')
      .find('li')
      .should('have.length', 1)
    cy.get('[aria-label="Templates List"] .pf-c-data-list__item-row button').click()
    cy.get('[data-cy="job-status"]').should('have.text', 'Running')
    // Issue: the job status does not change to successful unless page is refreshed
    // .get('[data-cy="job-status"]').should('have.text', 'Successful')
  })
})

context.skip('Launch a Job Template with prompts', function() {
  before(function() {
    cy.createOrReplace('job_templates', `JT-to-launch`).as('launch')
  })
  it('can launch job template with prompts', function() {
    cy.visit('/#/templates')
    cy.get('input[aria-label*="Search"]').type(`${this.launch.name}{enter}`)
    cy.get('[aria-label="Templates List"]')
      .find('li')
      .should('have.length', 1)
    cy.get('[aria-label="Templates List"] .pf-c-data-list__item-row button').click()
    cy.get('[data-cy="job-status"]').should('have.text', 'Running')
    cy.get('[data-cy="job-status"]').should('have.text', 'Successful')
  })
})
context.skip('Job Template form validation', function() {})
context.skip('Job Template form actions', function() {
  it('Can toggle the advanced section of the form', function() {})
  it('Persists variables saved in prompts', function() {})
  it('Has playbook typeahead functionality', function() {})
})
context.skip('Survey operations', function() {})
