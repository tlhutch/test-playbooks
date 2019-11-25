/*
 * Tests for search functionality.
 */

context('Navigation', function() {
  it('Can do basic filtering on a search bar', function() {
    cy.akit('organizations.create()').then(function(org) {
      cy.visit('/#/organizations')
      cy.get('input[type="search"]').type(org.name)
      cy.get('button[type="submit"]').click()

      // View search result and ensure link is functional
      cy.get(`#check-action-${org.id} > a > b`)
        .should('have.text', org.name)
        .click()
      cy.location().should(loc => {
        expect(loc.hash).to.eq(`#/organizations/${org.id}/details`)
      })
    })
  })
})
