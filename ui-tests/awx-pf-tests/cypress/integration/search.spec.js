/*
 * Tests for search functionality.
 */

context('Navigation', function() {
  it('Can do basic filtering on a search bar', function() {
    cy.akit('organizations.create()').then(function(org) {
      cy.visit('/#/organizations')
      cy.get('input[type="search"]').type(org.name)
      cy.get('[aria-label="Search submit button"]').click()

      // View search result and ensure link is functional
      cy.get(`#check-action-${org.id} > a > b`)
        .should('have.text', org.name)
        .click()
      cy.location().should(loc => {
        expect(loc.hash).to.eq(`#/organizations/${org.id}/details`)
      })
    })
  })
  it.skip('does not persist search filters between multiple lookups', function() {})
  it.skip('can perform more advanced search options', function() {})
})
