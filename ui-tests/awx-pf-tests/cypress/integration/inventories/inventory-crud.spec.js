/**
 * Verifies CRUD operations on inventories.
 */

context.skip('Empty list of inventories', function() {
  it('Shows the add button when there is an empty list of inventories', function() {})
})

context.skip('Inventory advanced search', function() {})
context('Reaches a 404', function() {
  it('reaches a 404 when trying to get the inventory list', function() {
    cy.visit('/#/inventories/inventory/999')

    // Assert that the Inventory is not found and a link to navigate to the list of inventories exist
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
    // Select the organization for the inventory
    cy.get('.pf-c-modal-box__footer button[class="pf-c-button pf-m-primary"]').click()
    cy.get('button[aria-label=Save]').click()
    // Assert that the inventory is created and is navigated to the Inventory Details page
    cy.get('[aria-label="Details"]').should('be.visible')
    cy.get('[class*="CardBody__TabbedCardBody"]').within(() => {
      cy.contains(`create-inv-${this.testID}`).should('exist')
    })
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
    // Assert that the page is navigated to the Inventory Details page and the details are updated
    cy.get('[aria-label="Details"]').should('be.visible')
    cy.get('[class*="CardBody__TabbedCardBody"]').within(() => {
      cy.contains(`edited-inv-${this.testID}`).should('exist')
    })
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
    // Assert that the inventory is deleted and there are no inventories that match the filter criteria
    cy.get('.pf-c-empty-state .pf-c-empty-state__body').should(
      'have.class',
      'pf-c-empty-state__body'
    )
  })
})
