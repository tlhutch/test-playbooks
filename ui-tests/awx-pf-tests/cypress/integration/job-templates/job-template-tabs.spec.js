/*
 * Tests for different tabs of a job template page.
 */
context('Job Template tabs', function() {
  before(function() {
    cy.createOrReplace('job_templates', 'jt').as('jt')
  })

  it('Can view a job template form and its tabs', function() {
    cy.visit(`#/templates/job_template/${this.jt.id}`)
    cy.get('.pf-c-breadcrumb__heading').should('have.text', 'Details')
    cy.get('[data-cy="jt-detail-name-value"]').should('have.text', 'jt')

    cy.get('button[id*="pf-tab-1"]').click() // TODO: better ID for each tab
    cy.get('.pf-c-breadcrumb__heading').should('have.text', 'Access')

    cy.get('button[id*="pf-tab-2"]').click()
    cy.get('.pf-c-breadcrumb__heading').should('have.text', 'Notifications')

    /*
		* TODO: The rest of these tabs aren't implemented yet.
		cy.get('button[id*="pf-tab-3"]').click()
		cy.get('.pf-c-breadcrumb__heading').should('have.text', 'Schedules')

		cy.get('button[id*="pf-tab-4"]').click()
		cy.get('.pf-c-breadcrumb__heading').should('have.text', 'Completed Jobs')

		cy.get('button[id*="pf-tab-5"]').click()
		cy.get('.pf-c-breadcrumb__heading').should('have.text', 'Survey')
		*/
  })
})
