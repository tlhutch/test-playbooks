/**
 * Verifies CRUD operations on job templates.
 */
context('Reaches a 404', function() {
  it('reaches a 404 when trying to get the JT list', function() {
    cy.server()
    cy.route({
      url: '**/api/v2/job_templates/*',
      status: 404,
      response: {},
    }).as('jt')
    cy.visit('/#/templates')
  })
})
context('Create and Edit Job Template', function() {
  before(function() {
    cy.createOrReplace('inventory', `create-jt-inv`).as('inv')
    cy.createOrReplace('projects', `create-jt-pro`).as('project')
  })

  it('can create a job template', function() {
    cy.visit('/#/templates')
    cy.get('button[aria-label=Add]').click()
    cy.get('a[href*="job_template/add"]').click()
    cy.get('#template-name').type(`create-jt-${this.testID}`)
    cy.get('#template-description').type(`Creation test for JTs. Test ID: ${this.testID}`)
    cy.get('#inventory-lookup').click()
    cy.get('input[aria-label*="Search text input"]').type(`${this.inv.name}{enter}	`)
    cy.get(`#selected-${this.inv.id}`).click()
    cy.get('[aria-label="Select Inventory"] button[class="pf-c-button pf-m-primary"]').click()
    cy.get('#project').click()
    cy.get('input[aria-label*="Search text input"]').type(`${this.project.name}{enter}	`)
    cy.get(`#selected-${this.project.id}`).click()
    cy.get('[aria-label="Select Project"] button[class="pf-c-button pf-m-primary"]').click()
    cy.get('#template-playbook').select('ping.yml')
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `create-jt-${this.testID}`)
  })

  it('can edit a job template', function() {
    cy.get('.pf-m-primary:nth-of-type(1)').click()
    cy.get('#template-name')
      .clear()
      .type(`edited-jt-${this.testID}`)
    cy.get('#template-description')
      .clear()
      .type(`Edited test for JTs. Test ID: ${this.testID}`)
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `edited-jt-${this.testID}`)
  })
})

context('Delete Job Template', function() {
  before(function() {
    cy.createOrReplace('job_templates', `JT-to-delete`).as('del')
  })

  it('can delete an job template', function() {
    cy.visit('/#/templates')
    cy.get('input[aria-label*="Search"]').type(`${this.del.name}{enter}	`)
    cy.wait(500)
    cy.get(`input[id="select-jobTemplate-${this.del.id}"][type="checkbox"]`).click()
    cy.get('button[aria-label="Delete"]').click()
    cy.get('button[aria-label="confirm delete"]').click()
    cy.get('.pf-c-empty-state .pf-c-empty-state__body').should(
      'have.class',
      'pf-c-empty-state__body'
    )
  })
})
