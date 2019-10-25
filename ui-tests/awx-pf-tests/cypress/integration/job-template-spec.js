/**
 * Verifies basic operations on a Job Template.
 */
context('Create and edit Job Template', function () {
  before(function() {
    cy.createOrReplace('inventory', `create-jt-inv`).as('inv');
    cy.createOrReplace('projects', `create-jt-pro`).as('project');

  }) 

  it('can create a job template', function () {
    cy
      .visit('/#/templates')
      .get('button[aria-label=Add]').click()
      .get('a[href*="job_template/add"]').click()
      .get('#template-name').type(`create-jt-${this.testID}`)
      .get('#template-description').type(`Creation test for JTs. Test ID: ${this.testID}`)
      .get('#inventory-lookup').click()
      .get('input[aria-label*="Search text input"]').type(`${this.inv.name}{enter}	`)
      .get(`#selected-${this.inv.id}`).click()
      .get('[aria-label="Select Inventory"] button[class="pf-c-button pf-m-primary"]').click()
      .get('#project').click()
      .get('input[aria-label*="Search text input"]').type(`${this.project.name}{enter}	`)
      .get(`#selected-${this.project.id}`).click()
      .get('[aria-label="Select Project"] button[class="pf-c-button pf-m-primary"]').click()
      cy.get('#template-playbook').select('ping.yml')
      .get('button[aria-label=Save]').click()
      .get('dd:nth-of-type(1)').should('have.text', `create-jt-${this.testID}`)
  })

  it('can edit a job template', function () {
    cy
      .get('.pf-m-primary:nth-of-type(1)').click()
      .get('#template-name').clear().type(`edited-jt-${this.testID}`)
      .get('#template-description').clear().type(`Edited test for JTs. Test ID: ${this.testID}`)
      .get('button[aria-label=Save]').click()
      .get('dd:nth-of-type(1)').should('have.text', `edited-jt-${this.testID}`)
  })

  it('reaches a 404 when trying to get the JT list', function() {
    cy.server()
    cy.route({
        url: '**/api/v2/job_templates/*',
        status: 404,
        response: {}
      }).as('jt')
    cy.visit('/#/templates')
  })
})

context('Delete Job Template', function () {
  before(function() {
    cy.createOrReplace('job_templates', `JT-to-delete`).as('del');
  })

  it('can delete an job template', function () {
      cy
        .visit('/#/templates')
        .get('input[aria-label*="Search"]').type(`${this.del.name}{enter}	`)
        .wait(500)
        .get(`input[id="select-jobTemplate-${this.del.id}"][type="checkbox"]`).click()
        .get('button[aria-label="Delete"]').click()
        .get('button[aria-label="confirm delete"]').click()
        .get('.pf-c-empty-state .pf-c-empty-state__body').should('have.class', 'pf-c-empty-state__body')
  })
})
