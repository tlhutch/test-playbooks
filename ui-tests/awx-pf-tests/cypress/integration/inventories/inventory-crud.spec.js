/**
 * Verifies CRUD operations on inventories.
 */
context('Reaches a 404', function() {
  it('reaches a 404 when trying to get the inventory list', function() {
    cy.visit('/#/inventories/inventory/999')
    cy.get('h1[class*="pf-c-title"]').should('have.text', 'Not Found')
    cy.get('.pf-c-empty-state__body a[href="#/inventories"]').should(
      'have.text',
      'View all Inventories.'
    )
  })
})
context('Create an Inventory', function() {
  before(function() {
    cy.createOrReplace('organizations', `create-inv-org`).as('org')
  })

  it('can create an inventory', function() {
    cy.visit('/#/inventories')
    cy.get('button[aria-label=Add]').click()
    cy.get('a[href*="/inventory/add/"]').click()
    cy.get('#inventory-name').type(`create-inv-${this.testID}`)
    cy.get('#inventory-description').type(`Creation test for Inventories. Test ID: ${this.testID}`)
    cy.get('#organization').click()
    cy.get('input[aria-label*="Search text input"]').type(`${this.org.name}{enter}`)
    cy.get(`#selected-${this.org.id}`).click()
    cy.get('.pf-c-modal-box__footer button[class="pf-c-button pf-m-primary"]').click()
    cy.get('button[aria-label=Save]').click()
    // This doesn't lead to the correct URL, issue open here: https://github.com/ansible/awx/issues/5652
    // cy.get('dd:nth-of-type(1)').should('have.text', `create-inv-${this.testID}`)
  })
})

context('Edit an Inventory', function() {
  before(function() {
    cy.createOrReplace('inventory', `inv-to-edit`).as('edit')
  })

  it('can edit an inventory', function() {
    cy.visit(`/#/inventories/inventory/${this.edit.id}`)
    cy.get(`a[href*="/${this.edit.id}/edit"]`).click()
    cy.get('#inventory-name')
      .clear()
      .type(`edited-inv-${this.testID}`)
    cy.get('#inventory-description')
      .clear()
      .type(`Edited test for inv. Test ID: ${this.testID}`)
    cy.get('button[aria-label=Save]').click()
    // This doesn't reflect the edited values, issue open here: https://github.com/ansible/awx/issues/5657
    //cy.get('dd:nth-of-type(1)').should('have.text', `edited-jt-${this.testID}`)
  })
})

context('Delete an Inventory', function() {
  before(function() {
    cy.createOrReplace('inventory', `inv-to-delete`).as('del')
  })

  it('can delete an inventory', function() {
    cy.visit('/#/inventories')
    cy.get('input[aria-label*="Search"]').type(`${this.del.name}{enter}`)
    cy.get('[aria-label="close"]')
    cy.get('[aria-label="Inventories List"]')
      .find('li')
      .should('have.length', 1)
    cy.get(`input[id="select-inventory-${this.del.id}"][type="checkbox"]:enabled`).click()
    cy.get('button[aria-label="Delete"]:enabled').click()
    cy.get('button[aria-label="confirm delete"]:enabled').click()
    cy.get('.pf-c-empty-state .pf-c-empty-state__body').should(
      'have.class',
      'pf-c-empty-state__body'
    )
  })
})
