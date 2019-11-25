/**
 * Example that shows two ways to call tower resources through the API.
 * Used as a sanity check to ensure calls to akit work.
 */

context('some page', function() {
  before(function() {
    // As an arbitrary akit function (uses the v2 object)
    cy.akit('organizations.create_or_replace(name="foo")').as('org')
    // Simpler helper function that just takes the resource type and name.
    // Both functions work exactly the same.
    cy.createOrReplace('teams', 'cool').as('team')
  })

  it('can make an organization and team object', function() {
    console.log(this.org)
    console.log(this.team)
  })
})
