/**
 * Verifies CRUD operations on inventory groups.
 */

context('Create an Inventory group', function() {
  before(function() {
    cy.createOrReplace('inventory', `inv`).as('inv')
  })

  it('can create an inventory group', function() {
    cy.visit(`/#/inventories/inventory/${this.inv.id}`)
    cy.get('button[aria-label="Groups"]').click()
    cy.get('.pf-c-empty-state .pf-c-title').should('have.text', 'No Items Found')
    cy.get('[aria-label="Add"]').click()
    cy.get('#inventoryGroup-name').type(`create-inv-group-${this.testID}`)
    cy.get('#inventoryGroup-description').type(
      `Creation test for Inventory groups. Test ID: ${this.testID}`
    )
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `create-inv-group-${this.testID}`)
  })
})

context('Edit an Inventory group', function() {
  before(function() {
    cy.akit('groups.get_or_create(inventory=v2.inventory.create_or_replace(name="abcde"))').as(
      'inv_group'
    )
    cy.akit('inventory.get_or_create(name="abcde")').as('inv')
  })

  it('can edit an inventory group', function() {
    cy.visit(`/#/inventories/inventory/${this.inv.id}`)
    cy.get('button[aria-label="Groups"]').click()
    cy.get('input[aria-label*="Search text input"]').type(`${this.inv_group.name}{enter}`)
    cy.get(`a[href*="groups/${this.inv_group.id}/edit"]`).click()
    cy.get('#inventoryGroup-name')
      .clear()
      .type(`edited-inv-group-${this.testID}`)
    cy.get('#inventoryGroup-description')
      .clear()
      .type(`Edited test for inv group. Test ID: ${this.testID}`)
    cy.get('button[aria-label=Save]').click()
    cy.get('dd:nth-of-type(1)').should('have.text', `edited-inv-group-${this.testID}`)
  })
})

context('Delete an Inventory group', function() {
  before(function() {
    cy.akit('groups.get_or_create(inventory=v2.inventory.create_or_replace(name="abcde"))').as(
      'inv_group'
    )
    cy.akit('inventory.get_or_create(name="abcde")').as('inv')
  })

  it('can delete an inventory group', function() {
    cy.visit(`/#/inventories/inventory/${this.inv.id}`)
    cy.get('button[aria-label="Groups"]').click()
    cy.get('input[aria-label*="Search text input"]').type(`${this.inv_group.name}{enter}`)
    cy.get('[aria-label="close"]')
    cy.get(`input[id="select-group-${this.inv_group.id}"][type="checkbox"]:enabled`).click()
    cy.get('button[aria-label="Delete"]:enabled').click()
    cy.get('label[for="radio-delete"]').click()
    cy.get('[aria-label="Delete Group"] button[aria-label="Delete"]:enabled').click()
    cy.get('.pf-c-empty-state .pf-c-empty-state__body').should(
      'have.class',
      'pf-c-empty-state__body'
    )
  })
})
